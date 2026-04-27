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
from metax.frameworks_and_drivers.pydanja_.pydanja_resource import MetaxDANJAResource
from metax_bootstrap import get_metax_lifespan_manager


class CategoryResource(BaseModel):
    name: str
    category_uuid: Annotated[
        UUID | None,
        SkipJsonSchema(),
        Field(
            default=None,
            json_schema_extra={"resource_id": True},
        ),
    ]


class CategoryDANJAResource(MetaxDANJAResource[CategoryResource]):
    pass


_CATEGORY_POST_OPENAPI_EXAMPLE: dict[str, Any] = {
    "data": {
        "type": "categoryresource",
        "attributes": {
            "name": "Electronics",
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
            Annotated[Body[CategoryDANJAResource], ...],
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
            ),
        )
        return created
