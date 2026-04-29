from http import HTTPStatus
from typing import ClassVar

from django_framework.metax.views.category.resources import (
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
from django_framework.metax.views.json_content_configs import JsonApiParser, JsonApiRenderer
from dmr import Path, Query, ResponseSpec, modify
from pydanja import DANJAError, DANJARelationship, DANJAResourceIdentifier, DANJASingleResource

from metax.core.domain.entities.category.aggregate_root_entity import Category
from metax.frameworks_and_drivers.pydanja_.pydanja_resource import RESOURCE_TYPE_CATEGORY_HELPER_WORD
from metax_bootstrap import get_metax_lifespan_manager


class CategoryResourceController(MetaxJsonApiController):
    parsers: ClassVar[list[JsonApiParser]] = [JsonApiParser()]
    renderers: ClassVar[list[JsonApiRenderer]] = [JsonApiRenderer()]

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
            self.__apply_helper_words_include(category=category, response_body=response_body)

        return response_body

    @staticmethod
    def __apply_helper_words_include(response_body: CategoryResponseBody, category: Category) -> None:
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
                        helper_word=helper_word.get_text(),
                        created_at=helper_word.get_created_at(),
                        updated_at=helper_word.get_updated_at(),
                    )
                ).data
            )
        response_body.data.relationships = {
            RESOURCE_TYPE_CATEGORY_HELPER_WORD: DANJARelationship(data=helper_word_resources_identifiers)
        }
        response_body.included = included
