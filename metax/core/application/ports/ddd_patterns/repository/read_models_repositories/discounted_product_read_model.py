from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import datetime

from metax.core.application.read_models.discounted_product import (
    DiscountedProductCategoryReadModel,
    DiscountedProductReadModel,
    DiscountedProductRetailerReadModel,
)
from metax.core.domain.entities.category.aggregate_root_entity import Category
from metax.core.domain.entities.retailer.aggregate_root_entity import Retailer


class DiscountedProductReadModelRepository(ABC):
    @abstractmethod
    async def add_many(self, discounted_products: list[DiscountedProductReadModel]) -> None:
        pass

    @abstractmethod
    async def add_one(self, discounted_product: DiscountedProductReadModel) -> None:
        pass

    @staticmethod
    def category_entity_to_read_fragment(category: Category) -> DiscountedProductCategoryReadModel:
        return DiscountedProductCategoryReadModel(
            uuid_=str(category.get_uuid()),
            created_at=category.get_created_at().isoformat(),
            updated_at=category.get_updated_at().isoformat(),
            name=category.get_name(),
        )

    @abstractmethod
    async def delete_older_than_and_return_deleted_count(self, date_limit: datetime) -> int:
        pass

    @abstractmethod
    def all(self) -> AsyncIterator[DiscountedProductReadModel]:
        """Concrete implementations use ``async def`` + ``yield`` (async generator)."""
        ...

    @abstractmethod
    async def get_all_count(self) -> int:
        pass

    @abstractmethod
    async def search_by_name(
        self,
        name: str,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[DiscountedProductReadModel], int]:
        """Return a page of products matching ``name`` and the total hit count for the query."""
        ...

    @abstractmethod
    async def get_by_uuid(self, uuid_: str) -> DiscountedProductReadModel:
        pass

    @staticmethod
    def retailer_entity_to_read_fragment(retailer: Retailer) -> DiscountedProductRetailerReadModel:
        return DiscountedProductRetailerReadModel(
            uuid_=str(retailer.get_uuid()),
            created_at=retailer.get_created_at().isoformat(),
            updated_at=retailer.get_updated_at().isoformat(),
            name=retailer.get_name(),
            home_page_url=retailer.get_home_page_url(),
            phone_number=retailer.get_phone_number(),
        )

    @abstractmethod
    async def update_categories(self, category: DiscountedProductCategoryReadModel) -> None:
        pass

    @abstractmethod
    async def update_retailers(self, retailer: DiscountedProductRetailerReadModel) -> None:
        pass
