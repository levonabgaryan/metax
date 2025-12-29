from abc import ABC, abstractmethod
from datetime import datetime

from backend.core.domain.entities.category_entity.category import Category
from backend.core.domain.entities.discounted_product_entity.discounted_product import DiscountedProduct
from backend.core.domain.entities.retailer_entity.retailer import Retailer


class DiscountedProductReadModelRepository(ABC):
    def __init__(self) -> None:
        self.seen: set[DiscountedProduct] = set()

    @staticmethod
    @abstractmethod
    async def sync_many_by_date(date: datetime) -> None:
        pass

    @abstractmethod
    async def delete_older_than_and_return_deleted_count(self, date_limit: datetime) -> int:
        pass

    @abstractmethod
    async def update_category(self, updated_category: Category) -> None:
        pass

    @abstractmethod
    async def update_retailer(self, updated_retailer: Retailer) -> None:
        pass
