from abc import ABC, abstractmethod
from datetime import datetime
from typing import AsyncIterator

from discount_service.core.domain.entities.discounted_product_entity.discounted_product import (
    DiscountedProduct,
)


class IDiscountedProductFactory(ABC):
    @abstractmethod
    def create_many_from_retailer(
        self, retailer_url: str, started_time: datetime, batch_size: int = 500
    ) -> AsyncIterator[list[DiscountedProduct]]:
        # https://mypy.readthedocs.io/en/stable/more_types.html#asynchronous-iterators
        pass
