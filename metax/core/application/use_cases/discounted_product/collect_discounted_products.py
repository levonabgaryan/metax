import logging
from typing import override
from uuid import UUID

from metax.core.application.event_handlers.event_bus import EventBus
from metax.core.application.ports.backend_patterns.provider.unit_of_work_provider import IUnitOfWorkProvider
from metax.core.application.ports.ddd_patterns.service.category_classifier_service import (
    CategoryClassifierService,
)
from metax.core.application.ports.design_patterns.factory.discounted_product_collector_service_creator import (
    DiscountedProductCollectorServiceCreator,
)
from metax.core.application.use_cases.base_use_case import UseCase
from metax.core.application.use_cases.discounted_product.dtos import (
    CollectDiscountedProductsRequest,
    CollectDiscountedProductsResponse,
)
from metax.core.domain.entities.category.aggregate_root_entity import Category
from metax.core.domain.entities.discounted_product.aggregate_root_entity import DiscountedProduct

logger = logging.getLogger(__name__)


class CollectDiscountedProducts(UseCase[CollectDiscountedProductsRequest]):
    def __init__(
        self,
        unit_of_work_provider: IUnitOfWorkProvider,
        event_bus: EventBus,
        discounted_product_collector_service_creator: DiscountedProductCollectorServiceCreator,
        batch_size_for_saving_discounted_products: int = 500,
        category_classifier: CategoryClassifierService | None = None,
        default_category_uuid: UUID | None = None,
    ) -> None:
        super().__init__(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
        self.__collector_creator = discounted_product_collector_service_creator
        self.__batch_size = batch_size_for_saving_discounted_products
        self.__classifier = category_classifier
        # When the retailer has a fixed category, every product is stamped with it directly and the
        # embedding classifier is skipped — no per-product embedding is spent on identifying it.
        self.__default_category_uuid = default_category_uuid

    @override
    async def handle_use_case(
        self, request: CollectDiscountedProductsRequest
    ) -> CollectDiscountedProductsResponse:
        logger.info("Use Case: %s | Status: STARTED", self.__class__.__name__)

        # Load categories once — only if the embedding classifier will actually run. A retailer with a
        # fixed ``default_category_uuid`` bypasses classification entirely, so we skip the load too.
        categories: list[Category] = []
        if self.__classifier is not None and self.__default_category_uuid is None:
            uow = await self._unit_of_work_provider.provide()
            async with uow:
                categories = await uow.category_repo.all()
            if categories:
                logger.info(
                    "Category classifier ready — %d categories: %s",
                    len(categories),
                    [c.get_name() for c in categories],
                )
            else:
                logger.info("No categories in DB — skipping classification")

        total_count = 0
        batch: list[DiscountedProduct] = []

        async for product in self.__collector_creator.do_collect():
            batch.append(product)
            if len(batch) >= self.__batch_size:
                await self.__classify_and_save(batch, categories)
                total_count += len(batch)
                batch = []

        if batch:
            await self.__classify_and_save(batch, categories)
            total_count += len(batch)

        # Stale rows from previous runs are pruned later, in the embedding step, once the freshly
        # collected rows are embedded — so search keeps serving the previous set until the new one
        # is ready (see the TaskIQ embedding task).
        logger.info("Use Case: %s | Status: SUCCESS | Total: %d", self.__class__.__name__, total_count)
        return CollectDiscountedProductsResponse(added_count=total_count)

    async def __classify_and_save(
        self, batch: list[DiscountedProduct], categories: list[Category]
    ) -> None:
        if self.__default_category_uuid is not None:
            # Retailer sells a single category: stamp it directly (distance 0.0 = certain, so these
            # rank first within the category) and skip the classifier — no embeddings are spent here.
            for product in batch:
                product.set_category_uuid(self.__default_category_uuid, distance=0.0)
            await self.__save_batch(batch)
            return
        if self.__classifier is not None and categories:
            try:
                await self.__classifier.classify_products(batch, categories)
            except Exception:
                logger.warning("Classification failed for batch, saving without categories", exc_info=True)
        await self.__save_batch(batch)

    async def __save_batch(self, batch: list[DiscountedProduct]) -> None:
        uow = await self._unit_of_work_provider.provide()
        async with uow:
            await uow.discounted_product_repo.add_many(batch)
            await uow.commit()
