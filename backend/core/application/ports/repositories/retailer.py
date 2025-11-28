from abc import ABC, abstractmethod
from uuid import UUID

from backend.core.domain.entities.retailer_entity.retailer import Retailer


class IRetailerRepository(ABC):
    @abstractmethod
    async def get_by_uuid(self, retailer_uuid: UUID) -> Retailer:
        pass

    @abstractmethod
    async def save(self, retailer: Retailer) -> None:
        pass
