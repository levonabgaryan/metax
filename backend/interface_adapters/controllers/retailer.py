from uuid import uuid4, UUID

from backend.core.application.commands_and_handlers.retailer import CreateRetailerCommand, UpdateRetailerCommand
from backend.core.application.patterns.message_buss import MessageBus
from backend.interface_adapters.patterns.empty_view_model import EmptyViewModel
from backend.interface_adapters.patterns.operation_result import OperationResult


class RetailerController:
    def __init__(self, message_bus: MessageBus) -> None:
        self.message_bus = message_bus

    async def create(self, name: str, url: str, phone_number: str) -> OperationResult[EmptyViewModel]:
        command = CreateRetailerCommand(retailer_uuid=uuid4(), name=name, url=url, phone_number=phone_number)
        await self.message_bus.handle(command)
        return OperationResult.from_succeeded_view_model(EmptyViewModel())

    async def update(
        self,
        retailer_uuid: UUID,
        retailer_name: str | None = None,
        retailer_url: str | None = None,
        retailer_phone_number: str | None = None,
    ) -> OperationResult[EmptyViewModel]:
        command = UpdateRetailerCommand(
            retailer_uuid=retailer_uuid,
            new_name=retailer_name,
            new_url=retailer_url,
            new_phone_number=retailer_phone_number,
        )
        await self.message_bus.handle(command)
        return OperationResult.from_succeeded_view_model(EmptyViewModel())
