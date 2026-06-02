from http import HTTPStatus
from typing import Annotated

from dmr import Body, Path, Query, ResponseSpec, modify
from dmr.openapi.objects import MediaTypeMetadata
from pydanja import DANJAError

from django_framework.metax.views.category.resources import (
    CATEGORY_POST_AND_PATCH_OPENAPI_EXAMPLE,
    CategoryPatchRequestBody,
    CategoryPath,
    CategoryResource,
    CategoryResponseBody,
    QueryParamsForResource,
)
from django_framework.metax.views.json_api_controller import MetaxJsonApiController
from metax.core.application.cud_services.category import (
    DeleteCategoryRequestDTO,
    DeleteCategoryService,
    UpdateCategoryRequestDTO,
    UpdateCategoryService,
)
from metax_bootstrap import METAX_LIFESPAN_MANAGER


class CategoryResourceController(MetaxJsonApiController):
    @modify(
        status_code=HTTPStatus.NO_CONTENT,
        tags=["Category"],
        extra_responses=[ResponseSpec(status_code=HTTPStatus.NOT_FOUND, return_type=DANJAError)],
    )
    async def delete(self, parsed_path: Path[CategoryPath]) -> None:
        container = METAX_LIFESPAN_MANAGER.get_metax_container()
        await DeleteCategoryService(
            unit_of_work_provider=container.get_unit_of_work_provider(),
            event_bus=await container.get_event_bus(),
        ).execute(DeleteCategoryRequestDTO(category_uuid=parsed_path.category_uuid))

    @modify(
        status_code=HTTPStatus.OK,
        tags=["Category"],
        extra_responses=[ResponseSpec(status_code=HTTPStatus.NOT_FOUND, return_type=DANJAError)],
    )
    async def get(
        self, parsed_path: Path[CategoryPath], parsed_query: Query[QueryParamsForResource]
    ) -> CategoryResponseBody:
        unit_of_work = METAX_LIFESPAN_MANAGER.get_metax_container().get_unit_of_work()
        async with unit_of_work as uow:
            category = await uow.category_repo.get_by_uuid(parsed_path.category_uuid)
            await uow.commit()
        return CategoryResponseBody.from_basemodel(
            resource=CategoryResource(
                category_uuid=category.get_uuid(),
                name=category.get_name(),
                created_at=category.get_created_at(),
                updated_at=category.get_updated_at(),
            )
        )

    @modify(
        status_code=HTTPStatus.OK,
        tags=["Category"],
        extra_responses=[
            ResponseSpec(status_code=HTTPStatus.NOT_FOUND, return_type=DANJAError),
            ResponseSpec(status_code=HTTPStatus.CONFLICT, return_type=DANJAError),
        ],
    )
    async def patch(
        self,
        parsed_path: Path[CategoryPath],
        parsed_body: Annotated[
            Body[CategoryPatchRequestBody], MediaTypeMetadata(example=CATEGORY_POST_AND_PATCH_OPENAPI_EXAMPLE)
        ],
    ) -> CategoryResponseBody:
        container = METAX_LIFESPAN_MANAGER.get_metax_container()
        response_dto = await UpdateCategoryService(
            unit_of_work_provider=container.get_unit_of_work_provider(),
            event_bus=await container.get_event_bus(),
        ).execute(
            UpdateCategoryRequestDTO(
                category_uuid=parsed_path.category_uuid,
                new_name=parsed_body.data.attributes.name,
            )
        )
        return CategoryResponseBody.from_basemodel(
            resource=CategoryResource(
                category_uuid=response_dto.category_uuid,
                name=response_dto.name,
                created_at=response_dto.created_at,
                updated_at=response_dto.updated_at,
            )
        )
