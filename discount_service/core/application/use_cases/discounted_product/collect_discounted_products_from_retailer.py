from discount_service.core.application.event_and_handlers.discounted_product.events import (
    NewDiscountedProductsFromRetailerCollected,
)
from discount_service.core.application.patterns.use_case_abc import UseCase
from discount_service.core.application.ports.patterns.discounted_product_factory import DiscountedProductFactory
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.core.application.use_cases.discounted_product.dtos import (
    CollectDiscountedProductsFromRetailerRequest,
    CollectDiscountedProductsFromRetailerResponse,
)


class CollectDiscountedProductsFromRetailer(
    UseCase[CollectDiscountedProductsFromRetailerRequest, CollectDiscountedProductsFromRetailerResponse]
):
    def __init__(
        self,
        unit_of_work: AbstractUnitOfWork,
        discounted_product_factory: DiscountedProductFactory,
    ) -> None:
        super().__init__(unit_of_work=unit_of_work)
        self.discounted_product_factory = discounted_product_factory

    async def execute(
        self, request: CollectDiscountedProductsFromRetailerRequest
    ) -> CollectDiscountedProductsFromRetailerResponse:
        added_count = 0

        async for discounted_products in self.discounted_product_factory.create_many_from_retailer(
            started_time=request.started_time
        ):
            async with self.unit_of_work as uow:
                await uow.discounted_product_repo.add_many(discounted_products)
                await uow.commit()
                added_count += len(discounted_products)

        self.unit_of_work.add_event(
            NewDiscountedProductsFromRetailerCollected(new_products_created_date=request.started_time)
        )
        return CollectDiscountedProductsFromRetailerResponse(added_count=added_count)
