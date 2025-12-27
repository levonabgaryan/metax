from dataclasses import dataclass
from datetime import datetime

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
    deleted_count: int


class CollectDiscountedProductsFromRetailer(
    UseCase[CollectDiscountedProductsFromRetailerRequest, CollectDiscountedProductsFromRetailerResponse]
):
    def __init__(self, unit_of_work: UnitOfWork, discounted_product_factory: IDiscountedProductFactory) -> None:
        super().__init__(unit_of_work=unit_of_work)
        self.unit_of_work = unit_of_work
        self.discounted_product_factory = discounted_product_factory

    async def execute(
        self, request: CollectDiscountedProductsFromRetailerRequest
    ) -> CollectDiscountedProductsFromRetailerResponse:
        added_count = 0

        async for discounted_products in self.discounted_product_factory.create_many_from_retailer(
            retailer_url=request.retailer_url
        ):
            async with self.unit_of_work as uow:
                await uow.repositories.discounted_product.add_many(discounted_products)
                await uow.commit()
                added_count += len(discounted_products)

        async with self.unit_of_work as uow:
            deleted_count = await uow.repositories.discounted_product.delete_older_than_and_return_deleted_count(
                date_limit=request.started_time
            )
            await uow.commit()

        return CollectDiscountedProductsFromRetailerResponse(added_count=added_count, deleted_count=deleted_count)
