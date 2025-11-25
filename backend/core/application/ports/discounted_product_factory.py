from abc import ABC, abstractmethod

from backend.core.domain.entities.discounted_product_entity.discounted_product import (
    DiscountedProduct,
)


class IDiscountedProductFactory(ABC):
    @abstractmethod
    async def create_one(self) -> DiscountedProduct:
        pass

    @abstractmethod
    async def create_many(self) -> list[DiscountedProduct]:
        pass
