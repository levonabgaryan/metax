from abc import ABC, abstractmethod
from datetime import datetime
from typing import AsyncIterator


from discount_service.core.domain.entities.discounted_product_entity.discounted_product import (
    DiscountedProduct,
)


class BaseDiscountedProductsCollectorService(ABC):
    @abstractmethod
    def collect_discounted_products(self, started_time: datetime) -> AsyncIterator[DiscountedProduct]:
        pass
