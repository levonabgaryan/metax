import uuid
from http import HTTPStatus
from typing import Annotated, Any, ClassVar
from uuid import UUID

from django_framework.metax.views.controllers_descriptors import BaseController
from django_framework.metax.views.json_content_configs import JsonApiParser, JsonApiRenderer
from dmr import Body, Controller, modify
from dmr.endpoint import Endpoint
from dmr.openapi.objects import MediaTypeMetadata
from dmr.plugins.pydantic import PydanticSerializer
from pydantic import BaseModel
from pydantic.fields import Field
from pydantic.json_schema import SkipJsonSchema

from metax.core.application.cud_services.category import (
    CreateCategoryRequestDTO,
    CreateCategoryService,
)
from metax.core.application.cud_services.category import (
    HelperWordPayload as CreateCategoryHelperWordPayload,
)
from metax.frameworks_and_drivers.pydanja_.pydanja_resources import MetaxDANJAResource
from metax_bootstrap import get_metax_lifespan_manager


class CategoryResource(BaseModel):
    category_name: str
    category_uuid: Annotated[
        UUID | None,
        SkipJsonSchema(),
        Field(
            default=None,
            json_schema_extra={"resource_id": True},
            exclude=True,
        ),
    ]


class CategoryDANJAResource(MetaxDANJAResource[CategoryResource]):
    pass


_CATEGORY_POST_OPENAPI_EXAMPLE: dict[str, Any] = {
    "data": {
        "type": "category",
        "attributes": {
            "name": "Electronics",
        },
        "relationships": {
            "categoryHelperWord": {
                "data": [
                    {"type": "categoryHelperWord", "lid": "word-1"},
                    {"type": "categoryHelperWord", "lid": "word-2"},
                ]
            }
        },
    },
    "included": [
        {"type": "categoryHelperWord", "lid": "word-1", "attributes": {"word": "alpen gold"}},
        {"type": "helper-words", "lid": "word-2", "attributes": {"word": "chocolate"}},
    ],
}


class CategoryController(Controller[PydanticSerializer]):
    endpoint_cls: ClassVar[type[Endpoint]] = BaseController
    parsers: ClassVar[list[JsonApiParser]] = [JsonApiParser()]
    renderers: ClassVar[list[JsonApiRenderer]] = [JsonApiRenderer()]

    @modify(
        status_code=HTTPStatus.CREATED,
        tags=["Category"],
    )
    async def post(
        self,
        parsed_body: Annotated[
            Body[CategoryDANJAResource],
            MediaTypeMetadata(example=_CATEGORY_POST_OPENAPI_EXAMPLE),
        ],
    ) -> CategoryDANJAResource:
        container = get_metax_lifespan_manager().get_di_container()
        patterns = container.patterns_container.container
        unit_of_work_provider = patterns.unit_of_work_provider()
        event_bus = await patterns.event_bus.async_()

        category_uuid = uuid.uuid7()

        category_name = parsed_body.resource.category_name
        helper_words_texts = []
        if parsed_body.included is not None:
            for resource_object in parsed_body.included:
                if resource_object.type == "categoryHelperWord":
                    helper_words_texts.append(resource_object.attributes["word"])

        request_dto = CreateCategoryRequestDTO(
            category_uuid=category_uuid,
            name=category_name,
            helper_words_payload=[
                CreateCategoryHelperWordPayload(text=helper_word_text) for helper_word_text in helper_words_texts
            ],
        )
        service = CreateCategoryService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
        await service.execute(request_dto)
        created = CategoryDANJAResource.from_basemodel(
            resource=CategoryResource(
                category_name=request_dto.name,
                category_uuid=request_dto.category_uuid,
            ),
        )
        return created
