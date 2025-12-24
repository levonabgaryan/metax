from backend.core.application.patterns.use_case_abc import UseCase, EmptyResponseDTO
from backend.core.application.ports.patterns.discounted_product_factory import IDiscountedProductFactory
from backend.core.application.ports.patterns.unit_of_work import UnitOfWork
from backend.core.application.use_cases.discounted_product.dtos import CollectDiscountedProductsFromRetailerRequest


class CollectDiscountedProductsFromRetailerUseCase(
    UseCase[CollectDiscountedProductsFromRetailerRequest, EmptyResponseDTO]
):
    def __init__(self, unit_of_work: UnitOfWork, discounted_product_factory: IDiscountedProductFactory) -> None:
        super().__init__(unit_of_work=unit_of_work)
        self.discounted_product_factory = discounted_product_factory

    async def execute(self, request: CollectDiscountedProductsFromRetailerRequest) -> EmptyResponseDTO:
        async with self.unit_of_work as uow:
            async for products in self.discounted_product_factory.create_many_from_retailer(request.retailer_url):
                await uow.repositories.discounted_product.add_many(products)
                await uow.commit()
            # event for updating view `message_bus.handle`
        return EmptyResponseDTO()
