from backend.core.application.patterns.result_type import Result
from backend.core.application.ports.repositories.discounted_product import IDiscountedProductRepository
from backend.core.application.use_cases.discounted_product.dtos import DeleteAllDiscountedProductsResponse


class DeleteAllDiscountedProductsUseCase:
    def __init__(self, discounted_product_repository: IDiscountedProductRepository) -> None:
        self.discounted_product_repository = discounted_product_repository

    async def execute(self) -> Result[DeleteAllDiscountedProductsResponse]:
        deleted_discounted_products_count = (
            await self.discounted_product_repository.delete_all_and_return_count_of_deleted()
        )
        response = DeleteAllDiscountedProductsResponse(deleted_discounted_products_count)
        return Result.from_success(response)
