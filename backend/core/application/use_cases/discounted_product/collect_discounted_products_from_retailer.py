from dataclasses import dataclass
from datetime import datetime

from backend.core.application.event_and_handlers.discounted_product.events import (
    NewDiscountedProductsFromRetailerCollected,
)
from backend.core.application.patterns.use_case_abc import UseCase, RequestDTO, ResponseDTO
from backend.core.application.ports.patterns.discounted_product_factory import IDiscountedProductFactory
from backend.core.application.ports.patterns.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class CollectDiscountedProductsFromRetailerRequest(RequestDTO):
    retailer_url: str
    started_time: datetime


@dataclass(frozen=True)
class CollectDiscountedProductsFromRetailerResponse(ResponseDTO):
    added_count: int


class CollectDiscountedProductsFromRetailer(
    UseCase[CollectDiscountedProductsFromRetailerRequest, CollectDiscountedProductsFromRetailerResponse]
):
    def __init__(self, unit_of_work: UnitOfWork, discounted_product_factory: IDiscountedProductFactory) -> None:
        super().__init__(unit_of_work=unit_of_work)
        self.discounted_product_factory = discounted_product_factory

    async def execute(
        self, request: CollectDiscountedProductsFromRetailerRequest
    ) -> CollectDiscountedProductsFromRetailerResponse:
        added_count = 0

        async for discounted_products in self.discounted_product_factory.create_many_from_retailer(
            retailer_url=request.retailer_url
        ):
            async with self.unit_of_work as uow:
                await uow.repositories.discounted_product.add_many_by_date(
                    discounted_products, started_time=request.started_time
                )
                await uow.commit()
                added_count += len(discounted_products)

        self.unit_of_work.add_event(
            NewDiscountedProductsFromRetailerCollected(new_products_created_date=request.started_time)
        )
        return CollectDiscountedProductsFromRetailerResponse(added_count=added_count)
