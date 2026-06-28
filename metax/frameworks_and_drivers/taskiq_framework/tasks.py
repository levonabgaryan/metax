from __future__ import annotations

import asyncio
import datetime as dt
import logging
import uuid

from metax.core.application.event_handlers.event_bus import EventBus
from metax.core.application.ports.backend_patterns.provider.unit_of_work_provider import IUnitOfWorkProvider
from metax.core.application.ports.ddd_patterns.repository.read_models_repositories.discounted_product_read_model import (  # noqa: E501
    DiscountedProductReadModelRepository,
)
from metax.core.application.ports.ddd_patterns.service.category_classifier_service import (
    CategoryClassifierService,
)
from metax.core.application.ports.design_patterns.factory.discounted_product_collector_service_creator import (
    DiscountedProductCollectorServiceCreator,
)
from metax.core.application.use_cases.discounted_product.collect_discounted_products import (
    CollectDiscountedProducts,
)
from metax.core.application.use_cases.discounted_product.dtos import CollectDiscountedProductsRequest
from metax.core.domain.entities.retailer.value_objects import RetailersNames, parse_retailer_name
from metax.frameworks_and_drivers.design_patterns.factories.discounted_product_collector_service_creators import (
    SasAmDiscountProductCollectorCreator,
    YerevanCityDiscountProductCollectorCreator,
)
from metax_bootstrap import METAX_CONFIGS, METAX_LIFESPAN_MANAGER
from metax_logger.request_id_filter import request_id_scope

from .broker import broker_
from .errors import NoRetailersError

logger = logging.getLogger(__name__)

# The daily refresh is split into two independently-tracked TaskIQ jobs so each step's
# success/failure is recorded separately in the result backend:
#   step 1 — collect today's discounts (rows stamped with this run's start time); on success it
#            enqueues step 2.
#   step 2 — embed every still-unembedded row, then publish the new set by deleting the previous
#            run's rows.
# The previous run's rows (already embedded) keep serving search until step 2 has embedded the new
# set and only then deletes them — a zero-downtime swap. If embedding fails, the delete never runs,
# so search keeps serving the previous set rather than going empty.

# Embedding hits the embeddings service, which can transiently fail (e.g. a ReadTimeout while the
# model loads into memory on a cold start). ``embed_pending`` is idempotent — it only fetches rows
# whose embedding is still NULL — so a pass that fails partway is safe to repeat: the next pass
# resumes on whatever is still NULL. We re-scan up to ``_EMBED_MAX_PASSES`` times and fail the job
# if anything is still unembedded after that.
_EMBED_MAX_PASSES = 3
_EMBED_RETRY_BACKOFF_SECONDS = 5.0  # multiplied by the pass number for a linear backoff


async def collect_discounted_products_from_all_retailers(
    unit_of_work_provider: IUnitOfWorkProvider,
    event_bus: EventBus,
    start_date_of_collecting: dt.datetime,
    category_classifier: CategoryClassifierService | None = None,
) -> None:
    uow = await unit_of_work_provider.provide()
    async with uow:
        retailers = [r async for r in uow.retailer_repo.all()]
    if not retailers:
        raise NoRetailersError

    tasks = []
    for retailer in retailers:
        retailer_key = retailer.get_name()
        collector_service_creator_class = RETAILER_NAME_DISCOUNTED_PRODUCT_COLLECTOR_SERVICE_CREATOR_MAP[
            parse_retailer_name(retailer_key)
        ]

        collector_service_creator: DiscountedProductCollectorServiceCreator
        if collector_service_creator_class is YerevanCityDiscountProductCollectorCreator:
            collector_service_creator = YerevanCityDiscountProductCollectorCreator(
                start_date_of_collecting=start_date_of_collecting,
                retailer=retailer,
            )
        elif collector_service_creator_class is SasAmDiscountProductCollectorCreator:
            collector_service_creator = SasAmDiscountProductCollectorCreator(
                start_date_of_collecting=start_date_of_collecting,
                retailer=retailer,
            )
        else:
            msg = f"Unsupported collector: {collector_service_creator_class!r}"
            raise NotImplementedError(msg)

        use_case = CollectDiscountedProducts(
            unit_of_work_provider=unit_of_work_provider,
            discounted_product_collector_service_creator=collector_service_creator,
            event_bus=event_bus,
            category_classifier=category_classifier,
        )
        tasks.append(use_case.handle_use_case(request=CollectDiscountedProductsRequest(
            start_date_of_collecting=start_date_of_collecting
        )))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for result in results:
        if isinstance(result, Exception):
            logger.error("Error during collection: %s", result, exc_info=result)


async def _taskiq_collect_discounted_products_from_all_retailers(request_id: str | None = None) -> None:
    effective_id = request_id or f"gen-{uuid.uuid7()}"
    with request_id_scope(effective_id):
        container = METAX_LIFESPAN_MANAGER.get_metax_container()

        classifier: CategoryClassifierService | None = None
        if METAX_CONFIGS.category_classification_enabled:
            classifier = container.get_category_classifier()
            logger.info("Embedding-based category classifier enabled")

        started_at = dt.datetime.now(tz=dt.UTC)
        await collect_discounted_products_from_all_retailers(
            unit_of_work_provider=container.get_unit_of_work_provider(),
            event_bus=await container.get_event_bus(),
            start_date_of_collecting=started_at,
            category_classifier=classifier,
        )

        # Step 1 done. Hand off to step 2 (embed + publish) as its own job so its success/failure is
        # tracked independently. ``collected_since`` tells step 2 which rows are the previous run's,
        # to delete once the new set is embedded. EMBED_AFTER_COLLECT=false leaves both the embedding
        # and the swap for a manual backfill (the previous run's rows stay live until then).
        if METAX_CONFIGS.embed_after_collect:
            await taskiq_embed_discounted_products.kiq(
                request_id=effective_id, collected_since=started_at.isoformat()
            )
            logger.info("Step 1 (collection): SUCCESS | enqueued step 2 (embed + publish)")
        else:
            logger.info(
                "Step 1 (collection): SUCCESS | step 2 SKIPPED (EMBED_AFTER_COLLECT=false) | "
                "run scripts/backfill_embeddings.py to embed later"
            )


@broker_.task(
    task_name="CollectDiscountedProducts",
    schedule=[{"cron": "0 21 * * *", "args": [None]}],
)
async def taskiq_collect_discounted_products_from_all_retailers(request_id: str | None = None) -> None:
    await _taskiq_collect_discounted_products_from_all_retailers(request_id=request_id)


async def embed_all_pending(repo: DiscountedProductReadModelRepository) -> int:
    """Embed every row whose ``name_embedding`` is NULL, re-scanning up to ``_EMBED_MAX_PASSES`` times.

    ``embed_pending`` is idempotent, so a pass that fails partway is safe to repeat — the next pass
    resumes on whatever is still NULL. After each pass we re-count the pending rows and stop as soon
    as none remain. Raises if any rows are still unembedded once the pass budget is spent, so the
    caller (the embedding job) is marked failed.

    Returns:
        The total number of rows embedded across all passes.

    Raises:
        RuntimeError: If any rows are still unembedded after ``_EMBED_MAX_PASSES`` passes.
    """
    total_embedded = 0
    remaining = 0
    last_error: Exception | None = None
    for attempt in range(1, _EMBED_MAX_PASSES + 1):
        try:
            total_embedded += await repo.embed_pending()
        except Exception as error:
            last_error = error
            logger.warning(
                "Step 2 (embedding): pass %d/%d failed (%r)", attempt, _EMBED_MAX_PASSES, error
            )
        remaining = await repo.count_pending()
        if remaining == 0:
            return total_embedded
        if attempt < _EMBED_MAX_PASSES:
            backoff = _EMBED_RETRY_BACKOFF_SECONDS * attempt
            logger.warning(
                "Step 2 (embedding): %d row(s) still unembedded after pass %d/%d; retrying in %.0fs",
                remaining,
                attempt,
                _EMBED_MAX_PASSES,
                backoff,
            )
            await asyncio.sleep(backoff)
    msg = f"{remaining} row(s) still unembedded after {_EMBED_MAX_PASSES} passes"
    raise RuntimeError(msg) from last_error


async def _taskiq_embed_discounted_products(
    request_id: str | None = None, collected_since: str | None = None
) -> None:
    effective_id = request_id or f"gen-{uuid.uuid7()}"
    with request_id_scope(effective_id):
        container = METAX_LIFESPAN_MANAGER.get_metax_container()
        repo = await container.get_discounted_product_read_model_repository()

        logger.info("Step 2 (embedding): STARTED")
        embedded_count = await embed_all_pending(repo)
        logger.info("Step 2 (embedding): SUCCESS | Embedded: [%s]", embedded_count)

        # Publish the new set: now that it is fully embedded and searchable, drop the previous run's
        # rows. Skipped for manual backfills (no ``collected_since``), which only fill in embeddings.
        if collected_since is not None:
            cutoff = dt.datetime.fromisoformat(collected_since)
            uow = await container.get_unit_of_work_provider().provide()
            async with uow:
                deleted = await uow.discounted_product_repo.delete_older_than_and_return_deleted_count(
                    date_limit=cutoff
                )
                await uow.commit()
            logger.info("Step 2 (publish): SUCCESS | removed [%s] row(s) from previous runs", deleted)


@broker_.task(task_name="EmbedDiscountedProducts")
async def taskiq_embed_discounted_products(
    request_id: str | None = None, collected_since: str | None = None
) -> None:
    await _taskiq_embed_discounted_products(request_id=request_id, collected_since=collected_since)


RETAILER_NAME_DISCOUNTED_PRODUCT_COLLECTOR_SERVICE_CREATOR_MAP: dict[
    RetailersNames, type[DiscountedProductCollectorServiceCreator]
] = {
    RetailersNames.YEREVAN_CITY: YerevanCityDiscountProductCollectorCreator,
    RetailersNames.SAS_AM: SasAmDiscountProductCollectorCreator,
}
