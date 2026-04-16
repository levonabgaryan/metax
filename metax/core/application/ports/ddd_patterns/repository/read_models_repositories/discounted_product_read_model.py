from abc import ABC, abstractmethod
from datetime import datetime
from typing import AsyncIterator

from metax.core.application.read_models.discounted_product import DiscountedProductReadModel
from metax.core.domain.entities.category.entity import Category
from metax.core.domain.entities.retailer.entity import Retailer


class IDiscountedProductReadModelRepository(ABC):
    @abstractmethod
    async def delete_older_than_and_return_deleted_count(self, date_limit: datetime) -> int:
        pass

    @abstractmethod
    async def update_category(self, updated_category: Category) -> None:
        pass

    @abstractmethod
    async def update_retailer(self, updated_retailer: Retailer) -> None:
        pass

    @abstractmethod
    async def get_all_count(self) -> int:
        pass

    @abstractmethod
    async def add_one(self, discounted_product: DiscountedProductReadModel) -> None:
        pass

    @abstractmethod
    async def add_many(self, discounted_products: list[DiscountedProductReadModel]) -> None:
        pass

    @abstractmethod
    def get_all(self) -> AsyncIterator[DiscountedProductReadModel]:
        pass

    @abstractmethod
    async def get_by_uuid(self, uuid_: str) -> DiscountedProductReadModel:
        pass

    @abstractmethod
    async def get_by_name_page(
        self,
        name: str,
        scroll_id: str | None = None,
        size: int = 50,
    ) -> tuple[list[DiscountedProductReadModel], str | None]:
        pass
