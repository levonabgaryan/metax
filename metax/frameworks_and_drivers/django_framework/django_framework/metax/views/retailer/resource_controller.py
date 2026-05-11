from http import HTTPStatus
from typing import Annotated

from dmr import Body, Path, ResponseSpec, modify
from dmr.openapi.objects import MediaTypeMetadata
from pydanja import DANJAError

from django_framework.metax.views.json_api_controller import MetaxJsonApiController
from django_framework.metax.views.retailer.resources import (
    RETAILER_POST_AND_PATCH_OPENAPI_EXAMPLE,
    RetailerPatchRequestBody,
    RetailerPath,
    RetailerResource,
    RetailerResponseBody,
)
from metax.core.application.cud_services.retailer import (
    DeleteRetailerRequestDTO,
    DeleteRetailerService,
    UpdateRetailerRequestDTO,
    UpdateRetailerService,
)
from metax_bootstrap import METAX_LIFESPAN_MANAGER


class RetailerResourceController(MetaxJsonApiController):
    @modify(
        status_code=HTTPStatus.NO_CONTENT,
        tags=["Retailer"],
        extra_responses=[ResponseSpec(status_code=HTTPStatus.NOT_FOUND, return_type=DANJAError)],
    )
    async def delete(self, parsed_path: Path[RetailerPath]) -> None:
        container = METAX_LIFESPAN_MANAGER.get_metax_container()
        unit_of_work_provider = container.get_unit_of_work_provider()
        event_bus = await container.get_event_bus()
        cud_service = DeleteRetailerService(
            unit_of_work_provider=unit_of_work_provider,
            event_bus=event_bus,
        )
        request_dto = DeleteRetailerRequestDTO(retailer_uuid=parsed_path.retailer_uuid)
        await cud_service.execute(request_dto)

    @modify(
        status_code=HTTPStatus.OK,
        tags=["Retailer"],
        extra_responses=[ResponseSpec(status_code=HTTPStatus.NOT_FOUND, return_type=DANJAError)],
    )
    async def get(self, parsed_path: Path[RetailerPath]) -> RetailerResponseBody:
        container = METAX_LIFESPAN_MANAGER.get_metax_container()
        unit_of_work = container.get_unit_of_work()
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
        extra_responses=[
            ResponseSpec(status_code=HTTPStatus.NOT_FOUND, return_type=DANJAError),
            ResponseSpec(status_code=HTTPStatus.CONFLICT, return_type=DANJAError),
        ],
    )
    async def patch(
        self,
        parsed_path: Path[RetailerPath],
        parsed_body: Annotated[
            Body[RetailerPatchRequestBody], MediaTypeMetadata(example=RETAILER_POST_AND_PATCH_OPENAPI_EXAMPLE)
        ],
    ) -> RetailerResponseBody:
        container = METAX_LIFESPAN_MANAGER.get_metax_container()
        unit_of_work_provider = container.get_unit_of_work_provider()
        event_bus = await container.get_event_bus()

        cud_service = UpdateRetailerService(
            unit_of_work_provider=unit_of_work_provider,
            event_bus=event_bus,
        )

        request_dto = UpdateRetailerRequestDTO(
            retailer_uuid=parsed_path.retailer_uuid,
            new_home_page_url=parsed_body.data.attributes.home_page_url,
            new_name=parsed_body.data.attributes.name,
            new_phone_number=parsed_body.data.attributes.phone_number,
        )
        response_dto = await cud_service.execute(request_dto)

        return RetailerResponseBody.from_basemodel(
            resource=RetailerResource(
                retailer_uuid=response_dto.retailer_uuid,
                name=response_dto.new_name,
                home_page_url=response_dto.new_home_page_url,
                phone_number=response_dto.new_phone_number,
                created_at=response_dto.created_at,
                updated_at=response_dto.updated_at,
            )
        )
