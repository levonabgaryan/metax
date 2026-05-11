from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from uuid import UUID

from metax.core.application.ports.ddd_patterns.repository.errors import EntityIsNotFoundError
from metax.core.domain.entities.retailer.aggregate_root_entity import Retailer


class RetailerRepository(ABC):
    async def add(self, retailer: Retailer) -> None:
        await self._add(retailer)

    @abstractmethod
    def all(self) -> AsyncIterator[Retailer]:
        pass

    async def delete_by_uuid(self, uuid_: UUID) -> None:
        deleted_uuid = await self._delete_by_uuid_and_return_uuid(uuid_)
        if deleted_uuid is None:
            raise EntityIsNotFoundError(
                entity_type="retailer",
                searched_field_name="uuid",
                searched_field_value=str(uuid_),
            )

    async def get_by_name(self, name: str) -> Retailer:
        retailer = await self._get_by_name(name=name)
        if retailer is None:
            raise EntityIsNotFoundError(
                entity_type="retailer",
                searched_field_name="name",
                searched_field_value=name,
            )
        return retailer

    async def get_by_uuid(self, uuid_: UUID) -> Retailer:
        retailer = await self._get_by_uuid(uuid_=uuid_)
        if retailer is None:
            raise EntityIsNotFoundError(
                entity_type="retailer",
                searched_field_name="uuid",
                searched_field_value=str(uuid_),
            )
        return retailer

    @abstractmethod
    async def list_paginated_and_total_count(self, limit: int, offset: int) -> tuple[int, list[Retailer]]:
        pass

    async def update(self, updated_retailer: Retailer) -> None:
        await self._update(updated_retailer)

    @abstractmethod
    async def _add(self, retailer: Retailer) -> None:
        """Adds a retailer entity.

        Raises:
            EntityAlreadyExistsError: If unique constraint is violated.
        """

    @abstractmethod
    async def _delete_by_uuid_and_return_uuid(self, uuid_: UUID) -> UUID | None:
        pass

    @abstractmethod
    async def _get_by_name(self, name: str) -> Retailer | None:
        pass

    @abstractmethod
    async def _get_by_uuid(self, uuid_: UUID) -> Retailer | None:
        pass

    @abstractmethod
    async def _update(self, updated_retailer: Retailer) -> None:
        """Updates a retailer entity.

        Raises:
            EntityAlreadyExistsError: If unique constraint is violated.
        """
