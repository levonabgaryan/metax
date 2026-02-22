from discount_service.core.application.event_and_handlers.discounted_product.events import (
    NewDiscountedProductsFromRetailerCollected,
)
from discount_service.core.application.patterns.services.discounted_products_collector import (
    BaseDiscountedProductsCollectorService,
)
from discount_service.core.application.patterns.use_case_abc import UseCase
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork

from discount_service.core.application.use_cases.discounted_product.dtos import (
    CollectDiscountedProductsFromRetailerRequest,
    CollectDiscountedProductsFromRetailerResponse,
)
from discount_service.core.domain.entities.discounted_product_entity.discounted_product import DiscountedProduct


class CollectDiscountedProductsFromRetailer(
    UseCase[CollectDiscountedProductsFromRetailerRequest, CollectDiscountedProductsFromRetailerResponse]
):
    def __init__(
        self,
        unit_of_work: AbstractUnitOfWork,
        discounted_product_collector_service: BaseDiscountedProductsCollectorService,
        batch_size_for_saving_discounted_products: int = 500,
    ) -> None:
        super().__init__(unit_of_work=unit_of_work)
        self.discounted_product_collector_service = discounted_product_collector_service
        self._batch_size_for_saving_discounted_products = batch_size_for_saving_discounted_products

    async def execute(
        self, request: CollectDiscountedProductsFromRetailerRequest
    ) -> CollectDiscountedProductsFromRetailerResponse:
        total_count = 0
        batch = []

        async for (
            discounted_product
        ) in self.discounted_product_collector_service.collect_discounted_products_from_retailer():
            batch.append(discounted_product)

            if len(batch) >= self._batch_size_for_saving_discounted_products:
                await self._save_batch(batch)
                total_count += len(batch)
                batch = []

        if batch:
            await self._save_batch(batch)
            total_count += len(batch)

        self.unit_of_work.add_event(
            NewDiscountedProductsFromRetailerCollected(new_products_created_date=request.started_time)
        )
        return CollectDiscountedProductsFromRetailerResponse(added_count=total_count)

    async def _save_batch(self, batch: list[DiscountedProduct]) -> None:
        async with self.unit_of_work as uow:
            await uow.discounted_product_repo.add_many(batch)
            await uow.commit()
