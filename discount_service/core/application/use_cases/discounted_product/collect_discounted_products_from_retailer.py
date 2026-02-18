from discount_service.core.application.event_and_handlers.discounted_product.events import (
    NewDiscountedProductsFromRetailerCollected,
)
from discount_service.core.application.patterns.discounted_products_collector_service_factory import (
    DiscountedProductsCollectorServiceCreator,
)
from discount_service.core.application.patterns.use_case_abc import UseCase
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork

from discount_service.core.application.use_cases.discounted_product.dtos import (
    CollectDiscountedProductsRequest,
    CollectDiscountedProductsResponse,
)


class CollectDiscountedProductsRetailer(
    UseCase[CollectDiscountedProductsRequest, CollectDiscountedProductsResponse]
):
    def __init__(
        self,
        unit_of_work: AbstractUnitOfWork,
        discounted_product_collector_factory: DiscountedProductsCollectorServiceCreator,
    ) -> None:
        super().__init__(unit_of_work=unit_of_work)
        self.discounted_product_collector_factory = discounted_product_collector_factory

    async def execute(self, request: CollectDiscountedProductsRequest) -> CollectDiscountedProductsResponse:
        service = await self.discounted_product_collector_factory.factory_method()
        collected_discounted_products_count = await service.collect_from_retailer_and_return_collected_count(
            started_time_of_collected=request.started_time
        )

        self.unit_of_work.add_event(
            NewDiscountedProductsFromRetailerCollected(new_products_created_date=request.started_time)
        )
        return CollectDiscountedProductsResponse(added_count=collected_discounted_products_count)
