from typing import AsyncIterator, override
from uuid import UUID

from metax.core.application.ports.repositories.entites_repositories.retailer import (
    RetailerRepository,
    RetailerFieldsToUpdate,
)
from metax.core.domain.entities.retailer_entity.retailer import Retailer
from django_framework.metax.models import RetailerModel


class DjangoPostgresqlRetailerRepository(RetailerRepository):
    @override
    async def _add(self, retailer: Retailer) -> None:
        await RetailerModel._default_manager.acreate(
            retailer_uuid=retailer.get_uuid(),
            name=retailer.get_name(),
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
    async def _get_by_name(self, retailer_name: str) -> Retailer | None:
        try:
            retailer_model = await RetailerModel._default_manager.aget(name=retailer_name)
        except RetailerModel.DoesNotExist:
            return None

        return self.__map_to_entity(model=retailer_model)

    @override
    async def _update(self, updated_retailer: Retailer, fields_to_update: RetailerFieldsToUpdate) -> None:
        update_data = {}

        if fields_to_update.name:
            update_data["name"] = updated_retailer.get_name()

        if fields_to_update.url:
            update_data["url"] = updated_retailer.get_home_page_url()

        if fields_to_update.phone_number:
            update_data["phone_number"] = updated_retailer.get_phone_number()

        if not update_data:
            return

        await RetailerModel._default_manager.filter(retailer_uuid=updated_retailer.get_uuid()).aupdate(
            **update_data
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
            name=model.name,
            home_page_url=model.url,
            phone_number=model.phone_number,
        )

    @override
    async def get_all(self) -> AsyncIterator[Retailer]:
        queryset = RetailerModel.objects.all().aiterator()

        async for model in queryset:
            yield self.__map_to_entity(model=model)
