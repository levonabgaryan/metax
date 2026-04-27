from datetime import datetime
from http import HTTPStatus
from typing import Annotated, Any, ClassVar
from uuid import UUID

from django_framework.metax.views.json_content_configs import JsonApiParser, JsonApiRenderer
from dmr import Body, Controller, modify
from dmr.openapi.objects import MediaTypeMetadata
from dmr.plugins.pydantic import PydanticSerializer
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from pydantic.fields import Field
from pydantic.json_schema import SkipJsonSchema

from metax.core.application.cud_services.category import (
    CreateCategoryRequestDTO,
    CreateCategoryService,
)
from metax.frameworks_and_drivers.pydanja_.pydanja_resource import (
    RESOURCE_TYPE_CATEGORY,
    MetaxDANJAResource,
)
from metax_bootstrap import get_metax_lifespan_manager


class CategoryResource(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"resource_name": RESOURCE_TYPE_CATEGORY},
        populate_by_name=True,
        alias_generator=to_camel,
    )
    category_uuid: Annotated[
        UUID | None,
        SkipJsonSchema(),
        Field(
            default=None,
            json_schema_extra={"resource_id": True},
            exclude=True,
        ),
    ]
    created_at: datetime | None = None
    updated_at: datetime | None = None
    name: str


class CategoryDANJAResource(MetaxDANJAResource[CategoryResource]):
    pass


_CATEGORY_POST_OPENAPI_EXAMPLE: dict[str, Any] = {
    "data": {
        "type": RESOURCE_TYPE_CATEGORY,
        "attributes": {
            "name": "Electronics",
        },
    },
}


class CategoryController(Controller[PydanticSerializer]):
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
        event_bus = await container.resources_container.container.event_bus.async_()

        category_name = parsed_body.resource.name

        request_dto = CreateCategoryRequestDTO(name=category_name, helper_words_payload=[])
        service = CreateCategoryService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
        response_dto = await service.execute(request_dto)
        created = CategoryDANJAResource.from_basemodel(
            resource=CategoryResource(
                name=response_dto.name,
                category_uuid=response_dto.category_uuid,
                created_at=response_dto.created_at,
                updated_at=response_dto.updated_at,
            ),
        )
        return created
