import logging
from typing import override

from metax.core.application.ddd_patterns.services.ollama_category_classifier_service import (
    OllamaCategoryClassifierService,
)
from metax.core.application.event_handlers.discounted_product.events import (
    NewDiscountedProductsFromRetailerCollected,
)
from metax.core.application.event_handlers.event_bus import EventBus
from metax.core.application.ports.backend_patterns.provider.unit_of_work_provider import IUnitOfWorkProvider
from metax.core.application.ports.design_patterns.factory.discounted_product_collector_service_creator import (
    DiscountedProductCollectorServiceCreator,
)
from metax.core.application.use_cases.base_use_case import UseCase
from metax.core.application.use_cases.discounted_product.dtos import (
    CollectDiscountedProductsRequest,
    CollectDiscountedProductsResponse,
)
from metax.core.domain.entities.discounted_product.aggregate_root_entity import DiscountedProduct

logger = logging.getLogger(__name__)


class CollectDiscountedProducts(UseCase[CollectDiscountedProductsRequest]):
    def __init__(
        self,
        unit_of_work_provider: IUnitOfWorkProvider,
        event_bus: EventBus,
        discounted_product_collector_service_creator: DiscountedProductCollectorServiceCreator,
        batch_size_for_saving_discounted_products: int = 500,
        category_classifier: OllamaCategoryClassifierService | None = None,
    ) -> None:
        super().__init__(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
        self.__collector_creator = discounted_product_collector_service_creator
        self.__batch_size = batch_size_for_saving_discounted_products
        self.__classifier = category_classifier

    @override
    async def handle_use_case(
        self, request: CollectDiscountedProductsRequest
    ) -> CollectDiscountedProductsResponse:
        logger.info("Use Case: %s | Status: STARTED", self.__class__.__name__)

        # Load categories once — only if Ollama classification is active.
        categories = []
        if self.__classifier is not None:
            uow = await self._unit_of_work_provider.provide()
            async with uow:
                categories = await uow.category_repo.all()
            if categories:
                logger.info(
                    "Ollama classifier ready — %d categories: %s",
                    len(categories),
                    [c.get_name() for c in categories],
                )
            else:
                logger.info("No categories in DB — skipping Ollama classification")

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

        await self._event_bus.emit(
            NewDiscountedProductsFromRetailerCollected(
                new_products_created_date=request.start_date_of_collecting
            )
        )
        logger.info("Use Case: %s | Status: SUCCESS | Total: %d", self.__class__.__name__, total_count)
        return CollectDiscountedProductsResponse(added_count=total_count)

    async def __classify_and_save(
        self, batch: list[DiscountedProduct], categories: list
    ) -> None:
        if self.__classifier is not None and categories:
            try:
                await self.__classifier.classify_products(batch, categories)
            except Exception:
                logger.warning("Ollama classification failed for batch, saving without categories", exc_info=True)
        await self.__save_batch(batch)

    async def __save_batch(self, batch: list[DiscountedProduct]) -> None:
        uow = await self._unit_of_work_provider.provide()
        async with uow:
            await uow.discounted_product_repo.add_many(batch)
            await uow.commit()
