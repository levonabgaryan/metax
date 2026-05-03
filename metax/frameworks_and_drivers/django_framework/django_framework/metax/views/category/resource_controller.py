from http import HTTPStatus
from typing import Annotated

from django_framework.metax.views.category.resources import (
    CATEGORY_POST_AND_PATCH_OPENAPI_EXAMPLE,
    CategoryPatchRequestBody,
    CategoryPath,
    CategoryResource,
    CategoryResponseBody,
    QueryParamsForResource,
)
from django_framework.metax.views.category_helper_word.resources import (
    CategoryHelperWordResource,
    CategoryHelperWordResponseBody,
)
from django_framework.metax.views.json_api_controller import MetaxJsonApiController
from dmr import Body, Path, Query, ResponseSpec, modify
from dmr.openapi.objects import MediaTypeMetadata
from pydanja import DANJAError, DANJARelationship, DANJAResourceIdentifier, DANJASingleResource

from metax.core.application.cud_services.category import UpdateCategoryRequestDTO, UpdateCategoryService
from metax.core.domain.entities.category.aggregate_root_entity import Category
from metax.frameworks_and_drivers.pydanja_.pydanja_resource import RESOURCE_TYPE_CATEGORY_HELPER_WORD
from metax_bootstrap import get_metax_lifespan_manager


class CategoryResourceController(MetaxJsonApiController):
    @modify(
        status_code=HTTPStatus.NO_CONTENT,
        tags=["Category"],
        extra_responses=[ResponseSpec(status_code=HTTPStatus.NOT_FOUND, return_type=DANJAError)],
    )
    async def delete(self, parsed_path: Path[CategoryPath]) -> None:
        category_uuid = parsed_path.category_uuid
        di_container = get_metax_lifespan_manager().get_di_container()
        unit_of_work = di_container.patterns_container.container.unit_of_work()

        async with unit_of_work as uow:
            await uow.category_repo.delete_by_uuid(category_uuid)
            await uow.commit()

    @modify(
        status_code=HTTPStatus.OK,
        tags=["Category"],
        extra_responses=[ResponseSpec(status_code=HTTPStatus.NOT_FOUND, return_type=DANJAError)],
    )
    async def get(
        self, parsed_path: Path[CategoryPath], parsed_query: Query[QueryParamsForResource]
    ) -> CategoryResponseBody:
        di_container = get_metax_lifespan_manager().get_di_container()
        unit_of_work = di_container.patterns_container.container.unit_of_work()

        async with unit_of_work as uow:
            category = await uow.category_repo.get_by_uuid(parsed_path.category_uuid)
            await uow.commit()

        response_body = CategoryResponseBody.from_basemodel(
            resource=CategoryResource(
                category_uuid=category.get_uuid(),
                name=category.get_name(),
                created_at=category.get_created_at(),
                updated_at=category.get_updated_at(),
            )
        )

        if parsed_query.include is not None:
            self.__fill_included_field(category=category, response_body=response_body)

        return response_body

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
        container = get_metax_lifespan_manager().get_di_container()
        unit_of_work_provider = container.patterns_container.container.unit_of_work_provider()
        event_bus = await container.resources_container.container.event_bus.async_()

        cud_service = UpdateCategoryService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
        request_dto = UpdateCategoryRequestDTO(
            category_uuid=parsed_path.category_uuid, new_name=parsed_body.data.attributes.name
        )
        response_dto = await cud_service.execute(request_dto)

        return CategoryResponseBody.from_basemodel(
            resource=CategoryResource(
                category_uuid=response_dto.category_uuid,
                name=response_dto.name,
                created_at=response_dto.created_at,
                updated_at=response_dto.updated_at,
            )
        )

    @staticmethod
    def __fill_included_field(response_body: CategoryResponseBody, category: Category) -> None:
        """Fill included field in response body by helper words resources."""
        helper_word_resources_identifiers: list[DANJAResourceIdentifier] = []
        included: list[
            DANJASingleResource[CategoryResource] | DANJASingleResource[CategoryHelperWordResource]
        ] = []

        for helper_word in category.get_helper_words():
            helper_word_resources_identifiers.append(
                DANJAResourceIdentifier(
                    id=str(helper_word.get_uuid()),
                    type=RESOURCE_TYPE_CATEGORY_HELPER_WORD,
                )
            )
            included.append(
                CategoryHelperWordResponseBody.from_basemodel(
                    resource=CategoryHelperWordResource(
                        helper_word_uuid=helper_word.get_uuid(),
                        helper_word_text=helper_word.get_helper_word_text(),
                        created_at=helper_word.get_created_at(),
                        updated_at=helper_word.get_updated_at(),
                    )
                ).data
            )
        response_body.data.relationships = {
            RESOURCE_TYPE_CATEGORY_HELPER_WORD: DANJARelationship(data=helper_word_resources_identifiers)
        }
        response_body.included = included
