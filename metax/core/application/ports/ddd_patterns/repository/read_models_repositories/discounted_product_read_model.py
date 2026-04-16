from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import datetime

from metax.core.application.read_models.discounted_product import DiscountedProductReadModel


class IDiscountedProductReadModelRepository(ABC):
    @abstractmethod
    async def delete_older_than_and_return_deleted_count(self, date_limit: datetime) -> int:
        pass

    @abstractmethod
    async def update_category_names_by_category_uuid(self, category_uuid: str, new_category_name: str) -> None:
        pass

    @abstractmethod
    async def update_retailer_names_by_retailer_uuid(self, retailer_uuid: str, new_retailer_name: str) -> None:
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
    async def get_by_name(
        self,
        name: str,
        cursor_: str | None = None,
        chunk_size: int = 50,
    ) -> tuple[list[DiscountedProductReadModel], str | None]:
        pass
