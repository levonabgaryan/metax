from dataclasses import dataclass
from uuid import UUID

from backend.core.application.patterns.use_case_abc import UseCase, RequestDTO, ResponseDTO
from backend.core.application.ports.patterns.discounted_product_factory import IDiscountedProductFactory
from backend.core.application.ports.patterns.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class CollectDiscountedProductsFromRetailerRequest(RequestDTO):
    retailer_uuid: UUID


@dataclass(frozen=True)
class CollectDiscountedProductsFromRetailerResponse(ResponseDTO):
    pass


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
        # logic
        return CollectDiscountedProductsFromRetailerResponse()
