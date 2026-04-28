from http import HTTPStatus
from typing import Annotated, ClassVar, override

from django.http import HttpResponse
from django_framework.metax.views.json_api_controller import MetaxJsonApiController
from django_framework.metax.views.json_content_configs import JsonApiParser, JsonApiRenderer
from django_framework.metax.views.retailer.resources import (
    RETAILER_POST_AND_PATCH_OPENAPI_EXAMPLE,
    RetailerListResponseBody,
    RetailerPostRequestBody,
    RetailerResource,
    RetailerResponseBody,
)
from dmr import Body, Controller, modify
from dmr.endpoint import Endpoint
from dmr.openapi.objects import MediaTypeMetadata
from dmr.plugins.pydantic import PydanticSerializer
from pydanja import DANJAError

from metax.core.application.cud_services.retailer import CreateRetailerRequestDTO, CreateRetailerService
from metax.core.application.ports.ddd_patterns.repository.errors import EntityIsNotFoundError
from metax_bootstrap import get_metax_lifespan_manager


class RetailerCollectionController(MetaxJsonApiController):
    parsers: ClassVar[list[JsonApiParser]] = [JsonApiParser()]
    renderers: ClassVar[list[JsonApiRenderer]] = [JsonApiRenderer()]

    def _collection_links(self) -> str:
        return self.request.build_absolute_uri(self.request.get_full_path())

    @modify(
        status_code=HTTPStatus.CREATED,
        tags=["Retailer"],
    )
    async def post(
        self,
        parsed_body: Annotated[
            Body[RetailerPostRequestBody], MediaTypeMetadata(example=RETAILER_POST_AND_PATCH_OPENAPI_EXAMPLE)
        ],
    ) -> RetailerResponseBody:
        container = get_metax_lifespan_manager().get_di_container()
        patterns = container.patterns_container.container
        unit_of_work_provider = patterns.unit_of_work_provider()
        event_bus = await container.resources_container.container.event_bus.async_()

        retailer_name = parsed_body.data.attributes.name
        home_page_url = parsed_body.data.attributes.home_page_url
        phone_number = parsed_body.data.attributes.phone_number

        request_dto = CreateRetailerRequestDTO(
            name=retailer_name,
            url=home_page_url,
            phone_number=phone_number,
        )

        service = CreateRetailerService(
            unit_of_work_provider=unit_of_work_provider,
            event_bus=event_bus,
        )
        response_dto = await service.execute(request_dto)

        return RetailerResponseBody.from_basemodel(
            resource=RetailerResource(
                retailer_uuid=response_dto.retailer_uuid,
                name=response_dto.name,
                home_page_url=response_dto.home_page_url,
                phone_number=response_dto.phone_number,
                created_at=response_dto.created_at,
                updated_at=response_dto.updated_at,
            )
        )

    @modify(
        status_code=HTTPStatus.OK,
        tags=["Retailer"],
    )
    async def get(self) -> RetailerListResponseBody:
        container = get_metax_lifespan_manager().get_di_container()
        unit_of_work = container.patterns_container.container.unit_of_work()
        async with unit_of_work as uow:
            all_retailers = uow.retailer_repo.get_all()
            await uow.commit()

        resources_list: list[RetailerResource] = [
            RetailerResource(
                retailer_uuid=r.get_uuid(),
                name=r.get_name(),
                home_page_url=r.get_home_page_url(),
                phone_number=r.get_phone_number(),
                created_at=r.get_created_at(),
                updated_at=r.get_updated_at(),
            )
            async for r in all_retailers
        ]

        response_body = RetailerListResponseBody.from_basemodel_list(
            resources=resources_list,
        )
        response_body.links = {"self": self._collection_links()}
        return response_body

    @override
    async def handle_async_error(
        self,
        endpoint: Endpoint,
        controller: Controller[PydanticSerializer],
        exc: Exception,
    ) -> HttpResponse:
        if isinstance(exc, EntityIsNotFoundError):
            return self.to_error(
                raw_data=DANJAError(code=exc.error_code, title=exc.title, detail=exc.details),
                status_code=HTTPStatus.NOT_FOUND,
            )

        return await super().handle_async_error(endpoint, controller, exc)
