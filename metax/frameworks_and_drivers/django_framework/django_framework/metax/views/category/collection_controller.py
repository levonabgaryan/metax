from http import HTTPStatus
from typing import Annotated

from django_framework.metax.views.category.resources import (
    CATEGORY_POST_AND_PATCH_OPENAPI_EXAMPLE,
    CategoryListResponseBody,
    CategoryPostRequestBody,
    CategoryResource,
    CategoryResponseBody,
    QueryParamsForCollection,
)
from django_framework.metax.views.category_helper_word.resources import (
    CategoryHelperWordResource,
    CategoryHelperWordResponseBody,
)
from django_framework.metax.views.json_api_controller import MetaxJsonApiController
from dmr import Body, Query, ResponseSpec, modify
from dmr.openapi.objects import MediaTypeMetadata
from pydanja import DANJAError, DANJARelationship, DANJAResourceIdentifier, DANJASingleResource

from metax.core.application.cud_services.category import (
    CreateCategoryRequestDTO,
    CreateCategoryService,
)
from metax.core.domain.entities.category.aggregate_root_entity import Category
from metax.frameworks_and_drivers.pydanja_.pydanja_resource import RESOURCE_TYPE_CATEGORY_HELPER_WORD
from metax_bootstrap import get_metax_lifespan_manager


class CategoryCollectionController(MetaxJsonApiController):
    @modify(
        status_code=HTTPStatus.OK,
        tags=["Category"],
    )
    async def get(self, parsed_query: Query[QueryParamsForCollection]) -> CategoryListResponseBody:
        container = get_metax_lifespan_manager().get_metax_container()
        unit_of_work = container.get_unit_of_work()

        async with unit_of_work as uow:
            total_count, paginated_list_categories = await uow.category_repo.list_paginated_and_total_count(
                limit=parsed_query.limit, offset=parsed_query.offset
            )
            await uow.commit()

        categories_resources_list = [
            CategoryResource(
                category_uuid=c.get_uuid(),
                name=c.get_name(),
                created_at=c.get_created_at(),
                updated_at=c.get_updated_at(),
            )
            for c in paginated_list_categories
        ]

        response_body = CategoryListResponseBody.from_basemodel_list(
            resources=categories_resources_list,
        )

        if parsed_query.include is not None and parsed_query.include != RESOURCE_TYPE_CATEGORY_HELPER_WORD:
            msg = (
                f"Unsupported include: {parsed_query.include}. Allowed value: {RESOURCE_TYPE_CATEGORY_HELPER_WORD}"
            )
            raise ValueError(msg)

        if parsed_query.include == RESOURCE_TYPE_CATEGORY_HELPER_WORD:
            self.__apply_helper_words_include(response_body, paginated_list_categories)

        response_body.links = self._build_pagination_links(
            self.request.build_absolute_uri(),
            offset=parsed_query.offset,
            limit=parsed_query.limit,
            total_count=total_count,
        )
        return response_body

    @modify(
        status_code=HTTPStatus.CREATED,
        tags=["Category"],
        extra_responses=[ResponseSpec(status_code=HTTPStatus.CONFLICT, return_type=DANJAError)],
    )
    async def post(
        self,
        parsed_body: Annotated[
            Body[CategoryPostRequestBody],
            MediaTypeMetadata(example=CATEGORY_POST_AND_PATCH_OPENAPI_EXAMPLE),
        ],
    ) -> CategoryResponseBody:
        container = get_metax_lifespan_manager().get_metax_container()
        unit_of_work_provider = container.get_unit_of_work_provider()
        event_bus = await container.get_event_bus()

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
        response_body.links = {"self": f"{self.request.build_absolute_uri()}/{response_dto.category_uuid}"}
        return response_body

    @staticmethod
    def __apply_helper_words_include(
        response_body: CategoryListResponseBody,
        paginated_list_categories: list[Category],
    ) -> None:
        included: list[
            DANJASingleResource[CategoryResource] | DANJASingleResource[CategoryHelperWordResource]
        ] = []
        category_data_by_id = {category_data.id: category_data for category_data in response_body.data}

        for category_entity in paginated_list_categories:
            helper_word_identifiers_for_category: list[DANJAResourceIdentifier] = []
            for helper_word in category_entity.get_helper_words():
                helper_word_identifiers_for_category.append(
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

            category_data = category_data_by_id.get(str(category_entity.get_uuid()))
            if category_data is not None:
                category_data.relationships = {
                    RESOURCE_TYPE_CATEGORY_HELPER_WORD: DANJARelationship(
                        data=helper_word_identifiers_for_category
                    )
                }

        response_body.included = included
