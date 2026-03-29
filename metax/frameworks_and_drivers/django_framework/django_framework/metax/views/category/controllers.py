import uuid
from http import HTTPStatus

from dmr.plugins.msgspec import MsgspecSerializer
from dmr import Body, Controller, modify

from django_framework.metax.views.category.request_body_models import CreateCategoryRequestBodyModel
from django_framework.metax.views.category.response_body_models import CreateCategoryResponseBodyModel
from metax.core.application.commands_handlers.category import (
    CreateCategoryCommand,
    CreateCategoryCommandHandler,
)
from metax.frameworks_and_drivers.di.metax_container import get_metax_container


class CreateCategoryController(
    Body[CreateCategoryRequestBodyModel],
    Controller[MsgspecSerializer],
):
    @modify(status_code=HTTPStatus.CREATED, tags=["Category"])
    async def post(self) -> CreateCategoryResponseBodyModel:
        container = get_metax_container()
        unit_of_work = await container.patterns_container.container.unit_of_work.async_()
        event_bus = container.patterns_container.container.event_bus()

        category_uuid = uuid.uuid4()
        cmd = CreateCategoryCommand(
            category_uuid=category_uuid,
            name=self.parsed_body.category_name,
            helper_words=frozenset(self.parsed_body.helper_words),
        )
        command_handler = CreateCategoryCommandHandler(unit_of_work=unit_of_work, event_bus=event_bus)
        await command_handler.handle_command(cmd)

        return CreateCategoryResponseBodyModel(category_uuid=category_uuid)
