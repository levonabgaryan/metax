import uuid
from http import HTTPStatus

from dmr import Controller, Body, modify
from dmr.plugins.msgspec import MsgspecSerializer

from django_framework.metax.views.retailer.request_body_models import CreateRetailerRequestBodyModel
from django_framework.metax.views.retailer.response_body_models import CreateRetailerResponseBodyModel
from metax.core.application.commands_handlers.retailer import CreateRetailerCommand, CreateRetailerCommandHandler
from metax.frameworks_and_drivers.di.metax_container import get_metax_container


class CreateRetailerController(Controller[MsgspecSerializer], Body[CreateRetailerRequestBodyModel]):
    @modify(
        status_code=HTTPStatus.CREATED,
        tags=["Retailer"],
    )
    async def post(self) -> CreateRetailerResponseBodyModel:
        container = get_metax_container()
        unit_of_work_provider = await container.patterns_container.container.unit_of_work_provider.async_()
        event_bus = container.patterns_container.container.event_bus()

        retailer_uuid = uuid.uuid4()
        cmd = CreateRetailerCommand(
            retailer_uuid=retailer_uuid,
            name=self.parsed_body.name,
            url=self.parsed_body.url,
            phone_number=self.parsed_body.phone_number,
        )

        command_handler = CreateRetailerCommandHandler(
            unit_of_work_provider=unit_of_work_provider,
            event_bus=event_bus,
        )
        await command_handler.handle_command(cmd)

        return CreateRetailerResponseBodyModel(retailer_uuid=retailer_uuid)
