from dataclasses import dataclass


@dataclass(frozen=True)
class CreateDiscountedProductsResponse:
    created_products_count: int


@dataclass(frozen=True)
class DeleteAllDiscountedProductsResponse:
    count_of_deleted: int
