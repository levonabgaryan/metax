from abc import ABC, abstractmethod
from typing import AsyncIterator
from uuid import UUID

from metax.core.application.ports.ddd_patterns.repository.errors import EntityIsNotFoundError
from metax.core.domain.entities.retailer.entity import Retailer
from metax.core.domain.entities.retailer.value_objects import RetailersNames


class RetailerRepository(ABC):
    async def get_by_uuid(self, retailer_uuid: UUID) -> Retailer:
        retailer = await self._get_by_uuid(retailer_uuid=retailer_uuid)
        if retailer is None:
            raise EntityIsNotFoundError(
                entity_name="retailer",
                searched_field_name="uuid",
                searched_field_value=str(retailer_uuid),
            )
        return retailer

    async def get_by_name(self, retailer_name: RetailersNames) -> Retailer:
        lookup = retailer_name.value if isinstance(retailer_name, RetailersNames) else retailer_name
        retailer = await self._get_by_name(retailer_name=retailer_name)
        if retailer is None:
            raise EntityIsNotFoundError(
                entity_name="retailer",
                searched_field_name="name",
                searched_field_value=lookup,
            )
        return retailer

    async def add(self, retailer: Retailer) -> None:
        await self._add(retailer)

    async def update(self, updated_retailer: Retailer) -> None:
        await self._update(updated_retailer)

    @abstractmethod
    async def _get_by_uuid(self, retailer_uuid: UUID) -> Retailer | None:
        pass

    @abstractmethod
    async def _add(self, retailer: Retailer) -> None:
        pass

    @abstractmethod
    async def _get_by_name(self, retailer_name: RetailersNames) -> Retailer | None:
        pass

    @abstractmethod
    async def _update(self, updated_retailer: Retailer) -> None:
        pass

    @abstractmethod
    def get_all(self) -> AsyncIterator[Retailer]:
        pass
