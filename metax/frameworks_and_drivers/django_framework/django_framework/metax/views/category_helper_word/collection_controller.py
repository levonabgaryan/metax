from http import HTTPStatus
from typing import Annotated, ClassVar
from uuid import UUID

from django_framework.metax.views.category_helper_word.resources import (
    CATEGORY_HELPER_WORD_POST_AND_PATCH_OPENAPI_EXAMPLE,
    CategoryHelperWordPostRequestBody,
    CategoryHelperWordResource,
    CategoryHelperWordResponseBody,
)
from django_framework.metax.views.json_api_controller import MetaxJsonApiController
from django_framework.metax.views.json_content_configs import JsonApiParser, JsonApiRenderer
from dmr import Body, modify
from dmr.exceptions import RequestSerializationError
from dmr.openapi.objects import MediaTypeMetadata

from metax.core.application.cud_services.category import (
    AddNewHelperWordsRequestDTO,
    AddNewHelperWordsService,
    HelperWordPayload,
)
from metax.frameworks_and_drivers.pydanja_.pydanja_resource import (
    RESOURCE_TYPE_CATEGORY,
)
from metax_bootstrap import get_metax_lifespan_manager


class CategoryHelperWordCollectionController(MetaxJsonApiController):
    parsers: ClassVar[list[JsonApiParser]] = [JsonApiParser()]
    renderers: ClassVar[list[JsonApiRenderer]] = [JsonApiRenderer()]

    @modify(
        status_code=HTTPStatus.CREATED,
        tags=["Category Helper word"],
    )
    async def post(
        self,
        parsed_body: Annotated[
            Body[CategoryHelperWordPostRequestBody],
            MediaTypeMetadata(example=CATEGORY_HELPER_WORD_POST_AND_PATCH_OPENAPI_EXAMPLE),
        ],
    ) -> CategoryHelperWordResponseBody:
        container = get_metax_lifespan_manager().get_di_container()
        patterns = container.patterns_container.container
        unit_of_work_provider = patterns.unit_of_work_provider()
        event_bus = await container.resources_container.container.event_bus.async_()

        unit_of_work = await unit_of_work_provider.provide()

        relationships = parsed_body.data.relationships
        if relationships is None:
            msg = f"Relationship block is required (link to '{RESOURCE_TYPE_CATEGORY}')"
            raise RequestSerializationError(msg)

        category_relationship = relationships.get(RESOURCE_TYPE_CATEGORY)
        if category_relationship is None:
            msg = f"Relationship '{RESOURCE_TYPE_CATEGORY}' is required"
            raise RequestSerializationError(msg)

        relationship_data = category_relationship.data
        if relationship_data is None or isinstance(relationship_data, list):
            msg = f"Relationship '{RESOURCE_TYPE_CATEGORY}.data' must contain a single resource identifier"
            raise RequestSerializationError(msg)

        category_identifier = relationship_data
        category_uuid = category_identifier.id
        helper_word = parsed_body.data.attributes.helper_word

        async with unit_of_work as uow:
            category = await uow.category_repo.get_by_uuid(uuid_=UUID(category_uuid))
            await uow.commit()

        request_dto = AddNewHelperWordsRequestDTO(
            category_uuid=category.get_uuid(),
            new_helper_word_payload=HelperWordPayload(text=helper_word),
        )
        cud_service = AddNewHelperWordsService(
            unit_of_work_provider=unit_of_work_provider,
            event_bus=event_bus,
        )
        response_dto = await cud_service.execute(request_dto)
        return CategoryHelperWordResponseBody.from_basemodel(
            resource=CategoryHelperWordResource(
                helper_word=response_dto.new_helper_word_payload.text,
                helper_word_uuid=response_dto.new_helper_word_payload.helper_word_uuid,
                created_at=response_dto.new_helper_word_payload.created_at,
                updated_at=response_dto.new_helper_word_payload.updated_at,
            )
        )
