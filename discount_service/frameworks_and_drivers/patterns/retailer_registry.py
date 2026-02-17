import uuid

from discount_service.core.application.ports.patterns.retailer_registry import RetailerRegistry
from discount_service.core.application.ports.repositories.errors.errors import EntityIsNotFoundError
from discount_service.core.domain.entities.retailer_entity.retailer import Retailer


class DjangoPostgresRetailerRegistry(RetailerRegistry):
    async def get_or_create_by_name(
        self, retailer_name: str, retailer_url: str, retailer_phone_number: str
    ) -> Retailer:
        try:
            return await self._retailer_repository.get_by_name(retailer_name)
        except EntityIsNotFoundError:
            new_retailer = Retailer(
                name=retailer_name,
                retailer_uuid=uuid.uuid4(),
                home_page_url=retailer_url,
                phone_number=retailer_phone_number,
            )
            await self._retailer_repository.add(new_retailer)
            return new_retailer
