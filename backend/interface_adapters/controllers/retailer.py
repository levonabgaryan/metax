from uuid import uuid4, UUID

from backend.core.application.commands_and_handlers.retailer import CreateRetailerCommand, UpdateRetailerCommand
from backend.core.application.patterns.message_buss import MessageBus
from backend.interface_adapters.empty_view_model import EmptyViewModel
from backend.interface_adapters.error_view_model import ErrorViewModel


class RetailerController:
    def __init__(self, message_bus: MessageBus) -> None:
        self.message_bus = message_bus

    async def create(self, name: str, url: str, phone_number: str) -> EmptyViewModel | ErrorViewModel:
        command = CreateRetailerCommand(retailer_uuid=uuid4(), name=name, url=url, phone_number=phone_number)
        await self.message_bus.handle(command)
        return EmptyViewModel()

    async def update(
        self,
        retailer_uuid: UUID,
        retailer_name: str | None = None,
        retailer_url: str | None = None,
        retailer_phone_number: str | None = None,
    ) -> EmptyViewModel | ErrorViewModel:
        command = UpdateRetailerCommand(
            retailer_uuid=retailer_uuid,
            retailer_name=retailer_name,
            retailer_url=retailer_url,
            retailer_phone_number=retailer_phone_number,
        )
        await self.message_bus.handle(command)
        return EmptyViewModel()
