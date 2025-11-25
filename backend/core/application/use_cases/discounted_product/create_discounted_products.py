from backend.core.application.patterns.result_type import Result
from backend.core.application.ports.discounted_product_factory import (
    IDiscountedProductFactory,
)
from backend.core.application.ports.repositories.discounted_product import (
    IDiscountedProductRepository,
)
from backend.core.application.use_cases.discounted_product.dtos import (
    CreateDiscountedProductsResponse,
)


class CreateDiscountedProductsUseCase:
    def __init__(
        self,
        discounted_product_repository: IDiscountedProductRepository,
        discounted_product_factory: IDiscountedProductFactory,
    ) -> None:
        self.discounted_product_repository = discounted_product_repository
        self.discounted_product_factory = discounted_product_factory

    async def execute(self) -> Result[CreateDiscountedProductsResponse]:
        discounted_products = await self.discounted_product_factory.create_many()
        await self.discounted_product_repository.save_many(discounted_products)
        response = CreateDiscountedProductsResponse(
            created_products_count=len(discounted_products),
        )
        return Result.from_success(response)
