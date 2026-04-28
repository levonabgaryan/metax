from http import HTTPStatus
from typing import Annotated, ClassVar

from django_framework.metax.views.category.resources import (
    CATEGORY_POST_AND_PATCH_OPENAPI_EXAMPLE,
    CategoryListResponseBody,
    CategoryPostRequestBody,
    CategoryResource,
    CategoryResponseBody,
)
from django_framework.metax.views.json_api_controller import MetaxJsonApiController
from django_framework.metax.views.json_content_configs import JsonApiParser, JsonApiRenderer
from dmr import Body, modify
from dmr.openapi.objects import MediaTypeMetadata

from metax.core.application.cud_services.category import (
    CreateCategoryRequestDTO,
    CreateCategoryService,
)
from metax_bootstrap import get_metax_lifespan_manager


class CategoryCollectionController(MetaxJsonApiController):
    parsers: ClassVar[list[JsonApiParser]] = [JsonApiParser()]
    renderers: ClassVar[list[JsonApiRenderer]] = [JsonApiRenderer()]

    @modify(
        status_code=HTTPStatus.CREATED,
        tags=["Category"],
    )
    async def post(
        self,
        parsed_body: Annotated[
            Body[CategoryPostRequestBody],
            MediaTypeMetadata(example=CATEGORY_POST_AND_PATCH_OPENAPI_EXAMPLE),
        ],
    ) -> CategoryResponseBody:
        container = get_metax_lifespan_manager().get_di_container()
        patterns = container.patterns_container.container
        unit_of_work_provider = patterns.unit_of_work_provider()
        event_bus = await container.resources_container.container.event_bus.async_()

        category_name = parsed_body.data.attributes.name

        request_dto = CreateCategoryRequestDTO(name=category_name, helper_words_payload=[])
        cud_service = CreateCategoryService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
        response_dto = await cud_service.execute(request_dto)
        response_body = CategoryResponseBody.from_basemodel(
            resource=CategoryResource(
                name=response_dto.name,
                category_uuid=response_dto.category_uuid,
                created_at=response_dto.created_at,
                updated_at=response_dto.updated_at,
            ),
        )
        return response_body

    @modify(
        status_code=HTTPStatus.OK,
        tags=["Category"],
    )
    async def get(self) -> CategoryListResponseBody:
        container = get_metax_lifespan_manager().get_di_container()
        patterns = container.patterns_container.container
        unit_of_work = patterns.unit_of_work()

        async with unit_of_work as uow:
            all_categories = await uow.category_repo.get_all()
            await uow.commit()

        resources_list = [
            CategoryResource(
                category_uuid=c.get_uuid(),
                name=c.get_name(),
                created_at=c.get_created_at(),
                updated_at=c.get_updated_at(),
            )
            for c in all_categories
        ]
        response_body = CategoryListResponseBody.from_basemodel_list(
            resources=resources_list,
        )
        return response_body
