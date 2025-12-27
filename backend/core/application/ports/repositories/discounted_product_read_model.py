from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from backend.core.domain.entities.discounted_product_entity.discounted_product import DiscountedProduct


class DiscountedProductReadModelRepository(ABC):
    def __init__(self) -> None:
        self.seen: set[DiscountedProduct] = set()

    @abstractmethod
    async def add_many_by_date(self, date: datetime) -> None:
        pass

    @abstractmethod
    async def delete_older_than_and_return_deleted_count(self, date_limit: datetime) -> int:
        pass

    @abstractmethod
    async def update_category_name(self, category_uuid: UUID, new_category_name: str) -> None:
        pass
