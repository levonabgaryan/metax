from typing import AsyncIterator, override
from uuid import UUID

from django_framework.metax.models import RetailerModel

from metax.core.application.ports.ddd_patterns.repository.entites_repositories.retailer import (
    RetailerRepository,
)
from metax.core.domain.entities.retailer.entity import Retailer
from metax.core.domain.entities.retailer.value_objects import RetailersNames


class DjangoPostgresqlRetailerRepository(RetailerRepository):
    @override
    async def _add(self, retailer: Retailer) -> None:
        await RetailerModel._default_manager.acreate(
            retailer_uuid=retailer.get_uuid(),
            name=retailer.get_name().value,
            url=retailer.get_home_page_url(),
            phone_number=retailer.get_phone_number(),
        )

    @override
    async def _get_by_uuid(self, retailer_uuid: UUID) -> Retailer | None:
        try:
            retailer_model = await RetailerModel._default_manager.aget(retailer_uuid=retailer_uuid)
        except RetailerModel.DoesNotExist:
            return None

        return self.__map_to_entity(model=retailer_model)

    @override
    async def _get_by_name(self, retailer_name: RetailersNames | str) -> Retailer | None:
        name_key = retailer_name.value if isinstance(retailer_name, RetailersNames) else retailer_name
        try:
            retailer_model = await RetailerModel._default_manager.aget(name=name_key)
        except RetailerModel.DoesNotExist:
            return None

        return self.__map_to_entity(model=retailer_model)

    @override
    async def _update(self, updated_retailer: Retailer) -> None:
        await RetailerModel._default_manager.filter(retailer_uuid=updated_retailer.get_uuid()).aupdate(
            name=updated_retailer.get_name().value,
            url=updated_retailer.get_home_page_url(),
            phone_number=updated_retailer.get_phone_number(),
        )

    @override
    async def get_all_retailers_urls(self) -> tuple[str, ...]:
        urls_query_set = RetailerModel.objects.values_list("url", flat=True).aiterator()
        urls = [url async for url in urls_query_set]
        return tuple(urls)

    @staticmethod
    def __map_to_entity(model: RetailerModel) -> Retailer:
        return Retailer(
            retailer_uuid=model.retailer_uuid,
            name=RetailersNames(model.name),
            home_page_url=model.url,
            phone_number=model.phone_number,
        )

    @override
    async def get_all(self) -> AsyncIterator[Retailer]:
        queryset = RetailerModel.objects.all().aiterator()

        async for model in queryset:
            yield self.__map_to_entity(model=model)
