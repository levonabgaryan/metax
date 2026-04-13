import logging
from typing import override

from metax.core.application.ddd_patterns.services.category_classifier_service import (
    CategoryClassifierService,
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
from metax.core.domain.ddd_patterns.general_value_objects import UUIDValueObject
from metax.core.domain.entities.discounted_product.entity import DiscountedProduct

logger = logging.getLogger(__name__)


class CollectDiscountedProducts(UseCase[CollectDiscountedProductsRequest]):
    def __init__(
        self,
        unit_of_work_provider: IUnitOfWorkProvider,
        event_bus: EventBus,
        discounted_product_collector_service_creator: DiscountedProductCollectorServiceCreator,
        category_classifier_service: CategoryClassifierService,
        batch_size_for_saving_discounted_products: int = 500,
    ) -> None:
        super().__init__(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
        self.__discounted_product_collector_service_creator = discounted_product_collector_service_creator
        self.__batch_size_for_saving_discounted_products = batch_size_for_saving_discounted_products
        self.__category_classifier_service = category_classifier_service

    @override
    async def handle_use_case(
        self, request: CollectDiscountedProductsRequest
    ) -> CollectDiscountedProductsResponse:
        logger.info(
            "Use Case: %s | Status: STARTED",
            self.__class__.__name__,
        )
        total_count = 0
        batch = []

        async for discounted_product in self.__discounted_product_collector_service_creator.do_collect():
            category = await self.__category_classifier_service.classify_category(
                discounted_product_name=discounted_product.get_name()
            )
            if category is not None:
                discounted_product.set_category_uuid(category_uuid=UUIDValueObject.create(category.get_uuid()))
            batch.append(discounted_product)

            if len(batch) >= self.__batch_size_for_saving_discounted_products:
                await self.__save_batch(batch)
                total_count += len(batch)
                batch = []

        if batch:
            await self.__save_batch(batch)
            total_count += len(batch)

        event = NewDiscountedProductsFromRetailerCollected(
            new_products_created_date=request.start_date_of_collecting
        )
        await self._event_bus.handle(event)

        logger.info(
            "Use Case: %s | Status: SUCCESS",
            self.__class__.__name__,
        )
        return CollectDiscountedProductsResponse(added_count=total_count)

    async def __save_batch(self, batch: list[DiscountedProduct]) -> None:
        uow = await self._unit_of_work_provider.create()
        async with uow:
            await uow.discounted_product_repo.add_many(batch)
            await uow.commit()
