from dataclasses import dataclass


@dataclass(frozen=True)
class CreateDiscountedProductsResponse:
    created_products_count: int
