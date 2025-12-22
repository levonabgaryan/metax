from abc import ABC, abstractmethod

from backend.core.domain.entities.discounted_product_entity.discounted_product import (
    DiscountedProduct,
)


class DiscountedProductRepository(ABC):
    def __init__(self) -> None:
        self.seen: set[DiscountedProduct] = set()

    @abstractmethod
    async def add_many(self, discounted_products: list[DiscountedProduct]) -> None:
        pass
