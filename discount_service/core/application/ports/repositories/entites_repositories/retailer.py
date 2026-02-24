from abc import ABC, abstractmethod
from typing import AsyncIterator
from uuid import UUID
from dataclasses import dataclass, field

from discount_service.core.application.ports.repositories.errors.error_codes import RepositoriesErrorCodes
from discount_service.core.application.ports.repositories.errors.errors import EntityIsNotFoundError
from discount_service.core.domain.entities.retailer_entity.retailer import Retailer


@dataclass
class RetailerFieldsToUpdate:
    name: bool = field(default=False)
    url: bool = field(default=False)
    phone_number: bool = field(default=False)


class RetailerRepository(ABC):
    async def get_by_uuid(self, retailer_uuid: UUID) -> Retailer:
        retailer = await self._get_by_uuid(retailer_uuid=retailer_uuid)
        if retailer is None:
            raise EntityIsNotFoundError(
                entity_name="retailer",
                searched_field_name="uuid",
                searched_field_value=str(retailer_uuid),
                error_code=RepositoriesErrorCodes.RETAILER_IS_NOT_FOUND,
            )
        return retailer

    async def get_by_name(self, retailer_name: str) -> Retailer:
        retailer = await self._get_by_name(retailer_name=retailer_name)
        if retailer is None:
            raise EntityIsNotFoundError(
                entity_name="retailer",
                searched_field_name="name",
                searched_field_value=retailer_name,
                error_code=RepositoriesErrorCodes.RETAILER_IS_NOT_FOUND,
            )
        return retailer

    async def add(self, retailer: Retailer) -> None:
        await self._add(retailer)

    async def update(self, updated_retailer: Retailer, fields_to_update: RetailerFieldsToUpdate) -> None:
        await self._update(updated_retailer, fields_to_update)

    @abstractmethod
    async def _get_by_uuid(self, retailer_uuid: UUID) -> Retailer | None:
        pass

    @abstractmethod
    async def _add(self, retailer: Retailer) -> None:
        pass

    @abstractmethod
    async def _get_by_name(self, retailer_name: str) -> Retailer | None:
        pass

    @abstractmethod
    async def _update(self, updated_retailer: Retailer, fields_to_update: RetailerFieldsToUpdate) -> None:
        pass

    @abstractmethod
    async def get_all_retailers_urls(self) -> tuple[str, ...]:
        pass

    @abstractmethod
    def get_all(self) -> AsyncIterator[Retailer]:
        pass
