from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from uuid import UUID

from metax.core.application.ports.ddd_patterns.repository.errors import EntityIsNotFoundError
from metax.core.domain.entities.retailer.aggregate_root_entity import Retailer


class RetailerRepository(ABC):
    async def get_by_uuid(self, uuid_: UUID) -> Retailer:
        retailer = await self._get_by_uuid(uuid_=uuid_)
        if retailer is None:
            raise EntityIsNotFoundError(
                entity_name="retailer",
                searched_field_name="uuid",
                searched_field_value=str(uuid_),
            )
        return retailer

    async def get_by_name(self, name: str) -> Retailer:
        retailer = await self._get_by_name(name=name)
        if retailer is None:
            raise EntityIsNotFoundError(
                entity_name="retailer",
                searched_field_name="name",
                searched_field_value=name,
            )
        return retailer

    async def add(self, retailer: Retailer) -> None:
        await self._add(retailer)

    async def update(self, updated_retailer: Retailer) -> None:
        await self._update(updated_retailer)

    @abstractmethod
    def get_all(self) -> AsyncIterator[Retailer]:
        pass

    @abstractmethod
    async def _get_by_uuid(self, uuid_: UUID) -> Retailer | None:
        pass

    @abstractmethod
    async def _add(self, retailer: Retailer) -> None:
        pass

    @abstractmethod
    async def _get_by_name(self, name: str) -> Retailer | None:
        pass

    @abstractmethod
    async def _update(self, updated_retailer: Retailer) -> None:
        pass
