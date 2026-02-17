from discount_service.core.application.event_and_handlers.discounted_product.events import (
    NewDiscountedProductsFromRetailerCollected,
)
from discount_service.core.application.patterns.use_case_abc import UseCase
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.core.application.services.discounted_products_collector import (
    DiscountedProductsCollectorService,
)
from discount_service.core.application.use_cases.discounted_product.dtos import (
    CollectDiscountedProductsRetailerRequest,
    CollectDiscountedProductsRetailerResponse,
)


class CollectDiscountedProductsRetailer(
    UseCase[CollectDiscountedProductsRetailerRequest, CollectDiscountedProductsRetailerResponse]
):
    def __init__(
        self,
        unit_of_work: AbstractUnitOfWork,
        discounted_product_collector: DiscountedProductsCollectorService,
    ) -> None:
        super().__init__(unit_of_work=unit_of_work)
        self.discounted_product_collector = discounted_product_collector

    async def execute(
        self, request: CollectDiscountedProductsRetailerRequest
    ) -> CollectDiscountedProductsRetailerResponse:
        collected_discounted_products_count = (
            await self.discounted_product_collector.collect_from_retailer_and_return_collected_count(
                started_time_of_collected=request.started_time
            )
        )

        self.unit_of_work.add_event(
            NewDiscountedProductsFromRetailerCollected(new_products_created_date=request.started_time)
        )
        return CollectDiscountedProductsRetailerResponse(added_count=collected_discounted_products_count)
