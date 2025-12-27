from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from backend.core.application.ports.repositories.errors.error_codes import RepositoriesErrorCodes
from backend.core.application.ports.repositories.errors.errors import EntityIsNotFoundError
from backend.core.domain.entities.discounted_product_entity.discounted_product import (
    DiscountedProduct,
)


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
    async def add_many(self, discounted_products: list[DiscountedProduct], started_time: datetime) -> None:
        pass

    @abstractmethod
    async def _get_by_uuid(self, discounted_product_uuid: UUID) -> DiscountedProduct | None:
        pass

    @abstractmethod
    async def delete_older_than_and_return_deleted_count(self, date_limit: datetime) -> int:
        pass
