import uuid
from http import HTTPStatus
from typing import Annotated, ClassVar
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

from metax.core.application.commands_handlers.category import (
    CreateCategoryCommand,
    CreateCategoryCommandHandler,
)
from metax.core.application.commands_handlers.category.create_category import (
    HelperWordPayload as CreateCategoryHelperWordPayload,
)
from metax.frameworks_and_drivers.pydanja_.pydanja_resources import MetaxDANJAResource
from metax_bootstrap import get_metax_lifespan_manager


class CategoryResource(BaseModel):
    category_name: str
    helper_words: list[str]
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


_CATEGORY_POST_OPENAPI_EXAMPLE: dict[str, object] = {
    "data": {
        "type": "category",
        "attributes": {
            "category_name": "Electronics",
            "helper_words": ["deals", "weekly"],
        },
    },
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

        resource_data = parsed_body.resource
        cmd = CreateCategoryCommand(
            category_uuid=category_uuid,
            name=resource_data.category_name,
            helper_words_payload=[
                CreateCategoryHelperWordPayload(text=helper_word) for helper_word in resource_data.helper_words
            ],
        )
        command_handler = CreateCategoryCommandHandler(
            unit_of_work_provider=unit_of_work_provider, event_bus=event_bus
        )
        await command_handler.handle_command(cmd)
        created = CategoryDANJAResource.from_basemodel(
            resource=CategoryResource(
                category_name=cmd.name,
                helper_words=[payload.text for payload in cmd.helper_words_payload],
                category_uuid=cmd.category_uuid,
            ),
        )
        return created
