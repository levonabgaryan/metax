from abc import ABC, abstractmethod
from datetime import datetime
from typing import AsyncIterator, NamedTuple
from uuid import UUID

from discount_service.core.application.ports.repositories.errors.error_codes import RepositoriesErrorCodes
from discount_service.core.application.ports.repositories.errors.errors import EntityIsNotFoundError
from discount_service.core.domain.entities.discounted_product_entity.discounted_product import (
    DiscountedProduct,
)


class DiscountedProductWithDetails(NamedTuple):
    entity: DiscountedProduct
    category_name: str | None
    retailer_name: str


class DiscountedProductRepository(ABC):
    def __init__(self) -> None:
        self.seen: set[DiscountedProduct] = set()

    async def get_by_uuid(self, discounted_product_uuid: UUID) -> DiscountedProduct:
        discounted_product = await self._get_by_uuid(discounted_product_uuid)
        if discounted_product is None:
            raise EntityIsNotFoundError(
                entity_name="discounted_product",
                searched_field_name="uuid",
                searched_field_value=str(discounted_product_uuid),
                error_code=RepositoriesErrorCodes.DISCOUNTED_PRODUCT_IS_NOT_FOUND,
            )
        self.seen.add(discounted_product)
        return discounted_product

    @abstractmethod
    async def add_many(self, discounted_products: list[DiscountedProduct]) -> None:
        pass

    @abstractmethod
    async def _get_by_uuid(self, discounted_product_uuid: UUID) -> DiscountedProduct | None:
        pass

    @abstractmethod
    async def delete_older_than_and_return_deleted_count(self, date_limit: datetime) -> int:
        pass

    @abstractmethod
    def get_all(self) -> AsyncIterator[DiscountedProduct]:
        # https://mypy.readthedocs.io/en/stable/more_types.html#asynchronous-iterators
        pass

    @abstractmethod
    def get_all_by_date(self, date_: datetime) -> AsyncIterator[DiscountedProductWithDetails]:
        pass
