from abc import ABC, abstractmethod
from uuid import UUID

from app.core.domain.entities.retailer_entity.retailer import Retailer


class IRetailerRepository(ABC):
    @abstractmethod
    async def get_by_uuid(self, retailer_uuid: UUID) -> Retailer:
        pass
