from abc import ABC, abstractmethod
from typing import AsyncIterator, TYPE_CHECKING

from backend.core.domain.entities.discounted_product_entity.discounted_product import (
    DiscountedProduct,
)


class IDiscountedProductFactory(ABC):
    @abstractmethod
    async def create_many_from_retailer(
        self, retailer_url: str, batch_size: int = 500
    ) -> AsyncIterator[list[DiscountedProduct]]:
        if TYPE_CHECKING:
            yield []
