import datetime as dt
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import UUID

from metax.core.application.ports.ddd_patterns.repository.errors import EntityIsNotFoundError
from metax.core.domain.entities.category.aggregate_root_entity import Category
from metax.core.domain.entities.discounted_product.aggregate_root_entity import (
    DiscountedProduct,
)
from metax.core.domain.entities.retailer.aggregate_root_entity import Retailer


@dataclass(frozen=True)
class DiscountedProductWithRelations:
    entity: DiscountedProduct
    retailer: Retailer
    category: Category | None


class DiscountedProductRepository(ABC):
    async def add_many(self, discounted_products: list[DiscountedProduct]) -> None:
        await self._add_many(discounted_products)

    @abstractmethod
    def all(self, chunk_size: int = 500) -> AsyncIterator[DiscountedProduct]:
        # https://mypy.readthedocs.io/en/stable/more_types.html#asynchronous-iterators
        pass

    @abstractmethod
    async def delete_older_than_and_return_deleted_count(self, date_limit: dt.datetime) -> int:
        pass

    @abstractmethod
    async def delete_by_retailer_uuid_and_return_deleted_count(self, retailer_uuid: UUID) -> int:
        """Delete all discounted products for ``retailer_uuid`` (e.g. before deleting the retailer)."""

    @abstractmethod
    async def delete_category_by_uuid(self, category_uuid: UUID) -> int:
        pass

    @abstractmethod
    def get_by_created_at(
        self, created_at: dt.datetime, chunk_size: int = 500
    ) -> AsyncIterator[DiscountedProductWithRelations]:
        pass

    async def get_by_uuid(self, uuid_: UUID) -> DiscountedProduct:
        discounted_product = await self._get_by_uuid(uuid_)
        if discounted_product is None:
            raise EntityIsNotFoundError(
                entity_type="discounted_product",
                searched_field_name="uuid",
                searched_field_value=str(uuid_),
            )
        return discounted_product

    @abstractmethod
    async def _add_many(self, discounted_products: list[DiscountedProduct]) -> None:
        """Adds discounted products.

        Raises:
            EntityAlreadyExistsError: If unique constraint is violated.
        """

    @abstractmethod
    async def _get_by_uuid(self, uuid_: UUID) -> DiscountedProduct | None:
        pass
