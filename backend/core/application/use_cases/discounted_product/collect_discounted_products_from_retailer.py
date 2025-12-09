from backend.core.application.patterns.message_buss import MessageBus
from backend.core.application.patterns.use_case_abc import UseCase, EmptyResponseDTO
from backend.core.application.ports.discounted_product_factory import IDiscountedProductFactory
from backend.core.application.use_cases.discounted_product.dtos import CollectDiscountedProductsFromRetailerRequest


class CollectDiscountedProductsFromRetailerUseCase(
    UseCase[CollectDiscountedProductsFromRetailerRequest, EmptyResponseDTO]
):
    def __init__(self, message_bus: MessageBus, discounted_product_factory: IDiscountedProductFactory) -> None:
        self.message_bus = message_bus
        self.discounted_product_factory = discounted_product_factory

    async def execute(self, request: CollectDiscountedProductsFromRetailerRequest) -> EmptyResponseDTO:
        async with self.message_bus.unit_of_work as uow:
            async for products in self.discounted_product_factory.create_many_from_retailer(request.retailer_url):
                await uow.repositories.discounted_products.add_many(products)
            await uow.commit()
            # event for updating view `message_bus.handle`
        return EmptyResponseDTO()
