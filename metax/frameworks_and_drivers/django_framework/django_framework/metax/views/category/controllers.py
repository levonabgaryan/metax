import uuid
from http import HTTPStatus
from typing import Self, override
from uuid import UUID

from dmr import Body, Controller, modify
from dmr.plugins.pydantic import PydanticSerializer
from pydanja import DANJAResource
from pydantic import BaseModel, Field

from metax.core.application.commands_handlers.category import (
    CreateCategoryCommand,
    CreateCategoryCommandHandler,
)
from metax.frameworks_and_drivers.di.metax_container import get_metax_container


class CategoryResource(BaseModel):
    category_name: str
    helper_words: list[str]
    category_uuid: UUID | None = Field(default=None, json_schema_extra={"resource_id": True})


class CategoryDANJAResource(DANJAResource[CategoryResource]):
    @override
    @classmethod
    def from_basemodel(
        cls,
        resource: CategoryResource,
        resource_name: str | None = None,
        resource_id: str | None = None,
    ) -> Self:
        created = super().from_basemodel(resource, resource_name, resource_id)
        if not isinstance(created, cls):
            msg = f"expected {cls.__name__}, got {type(created).__name__}"
            raise TypeError(msg)
        return created


class CategoryController(Controller[PydanticSerializer]):
    @modify(
        status_code=HTTPStatus.CREATED,
        tags=["Category"],
    )
    async def post(self, parsed_body: Body[CategoryDANJAResource]) -> CategoryDANJAResource:
        container = get_metax_container()
        patterns = container.patterns_container.container
        unit_of_work_provider = patterns.unit_of_work_provider()
        event_bus = await patterns.event_bus.async_()

        category_uuid = uuid.uuid4()

        resource_data = parsed_body.resource
        cmd = CreateCategoryCommand(
            category_uuid=category_uuid,
            name=resource_data.category_name,
            helper_words=frozenset(resource_data.helper_words),
        )
        command_handler = CreateCategoryCommandHandler(
            unit_of_work_provider=unit_of_work_provider, event_bus=event_bus
        )
        await command_handler.handle_command(cmd)

        created = CategoryDANJAResource.from_basemodel(
            resource=CategoryResource(
                category_name=cmd.name,
                helper_words=list(cmd.helper_words),
                category_uuid=category_uuid,
            ),
        )
        return created
