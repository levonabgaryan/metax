from http import HTTPStatus
from typing import Annotated, ClassVar

from django_framework.metax.views.json_content_configs import JsonApiParser, JsonApiRenderer
from django_framework.metax.views.retailer.resources import (
    RETAILER_POST_AND_PATCH_OPENAPI_EXAMPLE,
    RetailerPatchRequestBody,
    RetailerPath,
    RetailerResource,
    RetailerResponseBody,
)
from dmr import Body, Controller, Path, ResponseSpec, modify
from dmr.openapi.objects import MediaTypeMetadata
from dmr.plugins.pydantic import PydanticSerializer
from pydanja import DANJAError

from metax.core.application.cud_services.retailer import UpdateRetailerRequestDTO, UpdateRetailerService
from metax_bootstrap import get_metax_lifespan_manager


class RetailerResourceController(Controller[PydanticSerializer]):
    parsers: ClassVar[list[JsonApiParser]] = [JsonApiParser()]
    renderers: ClassVar[list[JsonApiRenderer]] = [JsonApiRenderer()]

    @modify(
        status_code=HTTPStatus.OK,
        tags=["Retailer"],
        extra_responses=[ResponseSpec(status_code=HTTPStatus.NOT_FOUND, return_type=DANJAError)],
    )
    async def get(self, parsed_path: Path[RetailerPath]) -> RetailerResponseBody:
        container = get_metax_lifespan_manager().get_di_container()
        unit_of_work = container.patterns_container.container.unit_of_work()
        async with unit_of_work as uow:
            retailer = await uow.retailer_repo.get_by_uuid(parsed_path.retailer_uuid)
            await uow.commit()

        return RetailerResponseBody.from_basemodel(
            resource=RetailerResource(
                retailer_uuid=retailer.get_uuid(),
                name=retailer.get_name(),
                home_page_url=retailer.get_home_page_url(),
                phone_number=retailer.get_phone_number(),
                created_at=retailer.get_created_at(),
                updated_at=retailer.get_updated_at(),
            )
        )

    @modify(
        status_code=HTTPStatus.OK,
        tags=["Retailer"],
        extra_responses=[ResponseSpec(status_code=HTTPStatus.NOT_FOUND, return_type=DANJAError)],
    )
    async def patch(
        self,
        parsed_path: Path[RetailerPath],
        parsed_body: Annotated[
            Body[RetailerPatchRequestBody], MediaTypeMetadata(example=RETAILER_POST_AND_PATCH_OPENAPI_EXAMPLE)
        ],
    ) -> RetailerResponseBody:
        container = get_metax_lifespan_manager().get_di_container()
        unit_of_work_provider = container.patterns_container.container.unit_of_work_provider()
        event_bus = await container.resources_container.container.event_bus.async_()

        cud_service = UpdateRetailerService(
            unit_of_work_provider=unit_of_work_provider,
            event_bus=event_bus,
        )

        request_dto = UpdateRetailerRequestDTO(
            retailer_uuid=parsed_path.retailer_uuid,
            new_url=parsed_body.data.attributes.home_page_url,
            new_name=parsed_body.data.attributes.name,
            new_phone_number=parsed_body.data.attributes.phone_number,
        )
        response_dto = await cud_service.execute(request_dto)

        return RetailerResponseBody.from_basemodel(
            resource=RetailerResource(
                retailer_uuid=response_dto.retailer_uuid,
                name=response_dto.new_name,
                home_page_url=response_dto.new_url,
                phone_number=response_dto.new_phone_number,
                created_at=response_dto.created_at,
                updated_at=response_dto.updated_at,
            )
        )

    @modify(
        status_code=HTTPStatus.NO_CONTENT,
        tags=["Retailer"],
        extra_responses=[ResponseSpec(status_code=HTTPStatus.NOT_FOUND, return_type=DANJAError)],
    )
    async def delete(self, parsed_path: Path[RetailerPath]) -> None:
        retailer_uuid = parsed_path.retailer_uuid
        container = get_metax_lifespan_manager().get_di_container()
        unit_of_work = container.patterns_container.container.unit_of_work()
        async with unit_of_work as uow:
            await uow.retailer_repo.delete_by_uuid(retailer_uuid)
            await uow.commit()
