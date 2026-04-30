from http import HTTPStatus
from typing import Annotated

from django_framework.metax.views.json_api_controller import MetaxJsonApiController
from django_framework.metax.views.retailer.resources import (
    RETAILER_POST_AND_PATCH_OPENAPI_EXAMPLE,
    QueryParamsForCollection,
    RetailerListResponseBody,
    RetailerPostRequestBody,
    RetailerResource,
    RetailerResponseBody,
)
from dmr import Body, Query, ResponseSpec, modify
from dmr.openapi.objects import MediaTypeMetadata
from pydanja import DANJAError

from metax.core.application.cud_services.retailer import CreateRetailerRequestDTO, CreateRetailerService
from metax_bootstrap import get_metax_lifespan_manager


class RetailerCollectionController(MetaxJsonApiController):
    @modify(
        status_code=HTTPStatus.CREATED,
        tags=["Retailer"],
        extra_responses=[
            ResponseSpec(status_code=HTTPStatus.CONFLICT, return_type=DANJAError),
        ],
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
        response_body = RetailerResponseBody.from_basemodel(
            resource=RetailerResource(
                retailer_uuid=response_dto.retailer_uuid,
                name=response_dto.name,
                home_page_url=response_dto.home_page_url,
                phone_number=response_dto.phone_number,
                created_at=response_dto.created_at,
                updated_at=response_dto.updated_at,
            )
        )
        response_body.links = {"self": f"{self.request.build_absolute_uri()}/{response_dto.retailer_uuid}"}

        return response_body

    @modify(
        status_code=HTTPStatus.OK,
        tags=["Retailer"],
    )
    async def get(self, parsed_query: Query[QueryParamsForCollection]) -> RetailerListResponseBody:
        container = get_metax_lifespan_manager().get_di_container()
        unit_of_work = container.patterns_container.container.unit_of_work()
        async with unit_of_work as uow:
            total_count, paginated_list_retailers = await uow.retailer_repo.list_paginated_and_total_count(
                limit=parsed_query.limit, offset=parsed_query.offset
            )
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
            for r in paginated_list_retailers
        ]

        response_body = RetailerListResponseBody.from_basemodel_list(
            resources=resources_list,
        )
        response_body.links = self._build_pagination_links(
            self.request.build_absolute_uri(),
            offset=parsed_query.offset,
            limit=parsed_query.limit,
            total_count=total_count,
        )
        return response_body
