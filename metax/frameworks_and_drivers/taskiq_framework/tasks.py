from __future__ import annotations

import asyncio
import datetime as dt
import logging
import uuid
from typing import TYPE_CHECKING, Protocol
from uuid import UUID

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
from metax.core.domain.entities.retailer.aggregate_root_entity import Retailer
from metax.core.domain.entities.retailer.value_objects import RetailersNames, parse_retailer_name
from metax.frameworks_and_drivers.design_patterns.factories.discounted_product_collector_service_creators import (
    SasAmDiscountProductCollectorCreator,
    TntesakanAmDiscountProductCollectorCreator,
    YerevanCityDiscountProductCollectorCreator,
)
from metax_bootstrap import METAX_CONFIGS, METAX_LIFESPAN_MANAGER
from metax_logger.request_id_filter import request_id_scope

from .broker import broker_
from .errors import NoRetailersError
from .locks import get_collection_lock

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from metax.frameworks_and_drivers.di.metax_container import MetaxContainer

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


def _build_collect_use_case_for_retailer(
    retailer: Retailer,
    unit_of_work_provider: IUnitOfWorkProvider,
    event_bus: EventBus,
    start_date_of_collecting: dt.datetime,
    category_classifier: CategoryClassifierService | None,
) -> CollectDiscountedProducts:
    """Wire the collection use case for a single retailer.

    Shared by the all-retailers run (one per retailer, collected concurrently) and the manual
    single-retailer run. Every collector creator in the map takes the same
    ``(start_date_of_collecting, retailer)`` constructor, so the map entry can be instantiated directly.

    Returns:
        The wired ``CollectDiscountedProducts`` use case for ``retailer``.
    """
    collector_service_creator_class = RETAILER_NAME_DISCOUNTED_PRODUCT_COLLECTOR_SERVICE_CREATOR_MAP[
        parse_retailer_name(retailer.get_name())
    ]
    collector_service_creator = collector_service_creator_class(
        start_date_of_collecting=start_date_of_collecting,
        retailer=retailer,
    )
    return CollectDiscountedProducts(
        unit_of_work_provider=unit_of_work_provider,
        discounted_product_collector_service_creator=collector_service_creator,
        event_bus=event_bus,
        category_classifier=category_classifier,
        default_category_uuid=retailer.get_default_category_uuid(),
    )


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

    tasks = [
        _build_collect_use_case_for_retailer(
            retailer=retailer,
            unit_of_work_provider=unit_of_work_provider,
            event_bus=event_bus,
            start_date_of_collecting=start_date_of_collecting,
            category_classifier=category_classifier,
        ).handle_use_case(
            request=CollectDiscountedProductsRequest(start_date_of_collecting=start_date_of_collecting)
        )
        for retailer in retailers
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for result in results:
        if isinstance(result, Exception):
            logger.error("Error during collection: %s", result, exc_info=result)


async def collect_discounted_products_for_retailer(
    unit_of_work_provider: IUnitOfWorkProvider,
    event_bus: EventBus,
    retailer_name: str,
    start_date_of_collecting: dt.datetime,
    category_classifier: CategoryClassifierService | None = None,
) -> UUID:
    """Collect a single retailer (for a manual re-run).

    Looks the retailer up by name (propagating ``EntityIsNotFoundError`` if it does not exist), then
    runs its collector.

    Returns:
        The retailer's UUID, so step 2 can scope its publish swap to this retailer only.
    """
    uow = await unit_of_work_provider.provide()
    async with uow:
        retailer = await uow.retailer_repo.get_by_name(retailer_name)

    use_case = _build_collect_use_case_for_retailer(
        retailer=retailer,
        unit_of_work_provider=unit_of_work_provider,
        event_bus=event_bus,
        start_date_of_collecting=start_date_of_collecting,
        category_classifier=category_classifier,
    )
    await use_case.handle_use_case(
        request=CollectDiscountedProductsRequest(start_date_of_collecting=start_date_of_collecting)
    )
    return retailer.get_uuid()


async def _run_collection_job_under_lock(
    effective_id: str,
    label: str,
    collect: Callable[[MetaxContainer, dt.datetime], Awaitable[UUID | None]],
) -> None:
    """Run one crawl (step 1) under the global collection lock and hand it off to step 2.

    Acquires the lock without blocking; if another crawl already holds it, this run is *skipped* (not
    queued) — the lock exists precisely to keep a manual and the nightly run from overlapping. On
    success the lock's release token is handed to the embed job (step 2), which releases it after the
    publish swap; the whole collect → embed → publish lifecycle is thus mutually exclusive. If step 2
    is not enqueued (collection failed, or ``EMBED_AFTER_COLLECT`` is off) the lock is released here.

    Args:
        effective_id: Request-id used to correlate this run's logs and the step-2 job it enqueues.
        label: Human-readable run description for log lines (e.g. ``"collection: retailer sas-am"``).
        collect: Runs the actual collection and returns the retailer UUID for a single-retailer run
            (so step 2 scopes its publish swap) or ``None`` for the all-retailers run (global swap).
    """
    with request_id_scope(effective_id):
        lock = get_collection_lock()
        token = await lock.acquire()
        if token is None:
            logger.warning(
                "Step 1 (%s): SKIPPED | another crawl already holds the global collection lock", label
            )
            return

        release_token: str | None = token
        try:
            container = METAX_LIFESPAN_MANAGER.get_metax_container()
            started_at = dt.datetime.now(tz=dt.UTC)
            retailer_uuid = await collect(container, started_at)

            # Hand off to step 2 (embed + publish) as its own job so its success/failure is tracked
            # independently. ``collected_since`` tells step 2 which rows are the previous run's, to
            # delete once the new set is embedded; ``retailer_uuid`` (single-retailer run) scopes that
            # delete so re-running one crawler never touches another retailer's live rows.
            if METAX_CONFIGS.embed_after_collect:
                await taskiq_embed_discounted_products.kiq(
                    request_id=effective_id,
                    collected_since=started_at.isoformat(),
                    retailer_uuid=str(retailer_uuid) if retailer_uuid is not None else None,
                    lock_token=token,
                )
                # Step 2 now owns the lock and releases it after publishing — don't release it here.
                release_token = None
                logger.info("Step 1 (%s): SUCCESS | enqueued step 2 (embed + publish)", label)
            else:
                logger.info(
                    "Step 1 (%s): SUCCESS | step 2 SKIPPED (EMBED_AFTER_COLLECT=false) | "
                    "run scripts/backfill_embeddings.py to embed later",
                    label,
                )
        finally:
            if release_token is not None:
                await lock.release(release_token)


async def _taskiq_collect_discounted_products_from_all_retailers(request_id: str | None = None) -> None:
    effective_id = request_id or f"gen-{uuid.uuid7()}"

    async def _collect(container: MetaxContainer, started_at: dt.datetime) -> None:
        # Category classification always runs; it no-ops by itself if no categories are seeded.
        await collect_discounted_products_from_all_retailers(
            unit_of_work_provider=container.get_unit_of_work_provider(),
            event_bus=await container.get_event_bus(),
            start_date_of_collecting=started_at,
            category_classifier=container.get_category_classifier(),
        )

    await _run_collection_job_under_lock(effective_id, "collection: all retailers", _collect)


@broker_.task(
    task_name="CollectDiscountedProducts",
    schedule=[{"cron": "0 21 * * *", "args": [None]}],
)
async def taskiq_collect_discounted_products_from_all_retailers(request_id: str | None = None) -> None:
    await _taskiq_collect_discounted_products_from_all_retailers(request_id=request_id)


async def _taskiq_collect_discounted_products_for_retailer(
    retailer_name: str, request_id: str | None = None
) -> None:
    effective_id = request_id or f"gen-{uuid.uuid7()}"

    async def _collect(container: MetaxContainer, started_at: dt.datetime) -> UUID:
        return await collect_discounted_products_for_retailer(
            unit_of_work_provider=container.get_unit_of_work_provider(),
            event_bus=await container.get_event_bus(),
            retailer_name=retailer_name,
            start_date_of_collecting=started_at,
            category_classifier=container.get_category_classifier(),
        )

    await _run_collection_job_under_lock(effective_id, f"collection: retailer {retailer_name}", _collect)


@broker_.task(task_name="CollectDiscountedProductsForRetailer")
async def taskiq_collect_discounted_products_for_retailer(
    retailer_name: str, request_id: str | None = None
) -> None:
    """Manual, on-demand re-run of a single retailer's crawler (no cron schedule).

    The nightly ``CollectDiscountedProducts`` job still refreshes every retailer; this exists so a
    single crawler can be re-run in isolation (e.g. after fixing one retailer's collector). It shares
    the global collection lock with the nightly run, so the two can never overlap.
    """
    await _taskiq_collect_discounted_products_for_retailer(
        retailer_name=retailer_name, request_id=request_id
    )


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
    request_id: str | None = None,
    collected_since: str | None = None,
    retailer_uuid: str | None = None,
    lock_token: str | None = None,
) -> None:
    effective_id = request_id or f"gen-{uuid.uuid7()}"
    with request_id_scope(effective_id):
        try:
            container = METAX_LIFESPAN_MANAGER.get_metax_container()
            repo = await container.get_discounted_product_read_model_repository()

            logger.info("Step 2 (embedding): STARTED")
            embedded_count = await embed_all_pending(repo)
            logger.info("Step 2 (embedding): SUCCESS | Embedded: [%s]", embedded_count)

            # Publish the new set: now that it is fully embedded and searchable, drop the previous
            # run's rows. Skipped for manual backfills (no ``collected_since``), which only fill in
            # embeddings. When ``retailer_uuid`` is set (a single-retailer re-run) the swap is scoped
            # to that retailer so other retailers' live rows — older than the cutoff but not
            # re-collected — are left alone.
            if collected_since is not None:
                cutoff = dt.datetime.fromisoformat(collected_since)
                uow = await container.get_unit_of_work_provider().provide()
                async with uow:
                    dp_repo = uow.discounted_product_repo
                    if retailer_uuid is not None:
                        deleted = await dp_repo.delete_older_than_by_retailer_and_return_deleted_count(
                            date_limit=cutoff, retailer_uuid=UUID(retailer_uuid)
                        )
                    else:
                        deleted = await dp_repo.delete_older_than_and_return_deleted_count(
                            date_limit=cutoff
                        )
                    await uow.commit()
                logger.info("Step 2 (publish): SUCCESS | removed [%s] row(s) from previous runs", deleted)
        finally:
            # Release the global collection lock the step-1 job handed us — the crawl lifecycle is now
            # complete (or failed). Manual backfills run without a token, so nothing is released then.
            if lock_token is not None:
                await get_collection_lock().release(lock_token)


@broker_.task(task_name="EmbedDiscountedProducts")
async def taskiq_embed_discounted_products(
    request_id: str | None = None,
    collected_since: str | None = None,
    retailer_uuid: str | None = None,
    lock_token: str | None = None,
) -> None:
    await _taskiq_embed_discounted_products(
        request_id=request_id,
        collected_since=collected_since,
        retailer_uuid=retailer_uuid,
        lock_token=lock_token,
    )


class _CollectorCreatorFactory(Protocol):
    """The shared constructor signature of every retailer's collector creator.

    Lets the map instantiate an entry with ``(start_date_of_collecting, retailer)`` in a type-safe
    way — the abstract base's ``__init__`` takes only ``start_date_of_collecting``, so typing the map
    against it would reject the ``retailer`` argument.
    """

    def __call__(
        self, start_date_of_collecting: dt.datetime, retailer: Retailer
    ) -> DiscountedProductCollectorServiceCreator: ...


RETAILER_NAME_DISCOUNTED_PRODUCT_COLLECTOR_SERVICE_CREATOR_MAP: dict[
    RetailersNames, _CollectorCreatorFactory
] = {
    RetailersNames.YEREVAN_CITY: YerevanCityDiscountProductCollectorCreator,
    RetailersNames.SAS_AM: SasAmDiscountProductCollectorCreator,
    RetailersNames.TNTESAKAN_AM: TntesakanAmDiscountProductCollectorCreator,
}
