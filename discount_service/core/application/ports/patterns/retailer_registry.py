from abc import ABC, abstractmethod

from discount_service.core.application.ports.repositories.entites_repositories.retailer import RetailerRepository
from discount_service.core.domain.entities.retailer_entity.retailer import Retailer


class RetailerRegistry(ABC):
    def __init__(self, retailer_repository: RetailerRepository):
        self._retailer_repository = retailer_repository

    @abstractmethod
    async def get_or_create_by_name(
        self, retailer_name: str, retailer_url: str, retailer_phone_number: str
    ) -> Retailer:
        pass
