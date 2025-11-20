from abc import ABC, abstractmethod
from uuid import UUID

from app.core.domain.entities.discounted_product_entity.discounted_product import (
    DiscountedProduct,
)


class IDiscountedProductRepository(ABC):
    @abstractmethod
    async def get_by_uuid(self, discounted_product_uuid: UUID) -> DiscountedProduct:
        pass

    @abstractmethod
    async def get_by_category_uuid(self, category_uuid: UUID) -> list[DiscountedProduct]:
        pass

    @abstractmethod
    async def save_many(self, discounted_products: list[DiscountedProduct]) -> None:
        pass
