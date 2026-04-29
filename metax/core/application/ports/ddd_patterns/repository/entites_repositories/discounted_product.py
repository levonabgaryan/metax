from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from metax.core.application.ports.ddd_patterns.repository.errors import EntityIsNotFoundError
from metax.core.domain.entities.discounted_product.aggregate_root_entity import (
    DiscountedProduct,
)


@dataclass(frozen=True)
class DiscountedProductWithDetails:
    entity: DiscountedProduct
    category_name: str | None
    retailer_name: str


class DiscountedProductRepository(ABC):
    async def get_by_uuid(self, uuid_: UUID) -> DiscountedProduct:
        discounted_product = await self._get_by_uuid(uuid_)
        if discounted_product is None:
            raise EntityIsNotFoundError(
                entity_name="discounted_product",
                searched_field_name="uuid",
                searched_field_value=str(uuid_),
            )
        return discounted_product

    @abstractmethod
    async def add_many(self, discounted_products: list[DiscountedProduct]) -> None:
        pass

    @abstractmethod
    async def delete_older_than_and_return_deleted_count(self, date_limit: datetime) -> int:
        pass

    @abstractmethod
    def all(self, chunk_size: int = 500) -> AsyncIterator[DiscountedProduct]:
        # https://mypy.readthedocs.io/en/stable/more_types.html#asynchronous-iterators
        pass

    @abstractmethod
    def get_by_created_at(
        self, created_at: datetime, chunk_size: int = 500
    ) -> AsyncIterator[DiscountedProductWithDetails]:
        pass

    @abstractmethod
    async def _get_by_uuid(self, uuid_: UUID) -> DiscountedProduct | None:
        pass
