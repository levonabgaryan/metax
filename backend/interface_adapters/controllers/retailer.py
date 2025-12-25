from uuid import uuid4, UUID

from backend.core.application.commands_and_handlers.retailer import CreateRetailerCommand, UpdateRetailerCommand
from backend.core.application.patterns.message_buss import MessageBus
from backend.core.application.patterns.use_case_abc import GenericResponseDTO
from backend.interface_adapters.ports.presenters.base_presenter import BasePresenter
from backend.interface_adapters.patterns.empty_view_model import EmptyViewModel
from backend.interface_adapters.patterns.operation_result import OperationResult
from backend.interface_adapters.view_models.retailer import RetailerEntityViewModel


class RetailerController:
    def __init__(
        self,
        message_bus: MessageBus,
        retailer_presenter: BasePresenter[RetailerEntityViewModel, GenericResponseDTO],
    ) -> None:
        self.message_bus = message_bus
        self.retailer_presenter = retailer_presenter

    async def create(self, name: str, url: str, phone_number: str) -> OperationResult[EmptyViewModel]:
        command = CreateRetailerCommand(retailer_uuid=uuid4(), name=name, url=url, phone_number=phone_number)
        await self.message_bus.handle(command)
        view_model = self.retailer_presenter.present()
        return OperationResult.from_succeeded_view_model(view_model)

    async def update(
        self,
        retailer_uuid: str,
        new_name: str | None = None,
        new_url: str | None = None,
        new_phone_number: str | None = None,
    ) -> OperationResult[EmptyViewModel]:
        command = UpdateRetailerCommand(
            retailer_uuid=UUID(retailer_uuid),
            new_name=new_name,
            new_url=new_url,
            new_phone_number=new_phone_number,
        )
        await self.message_bus.handle(command)
        view_model = self.retailer_presenter.present()
        return OperationResult.from_succeeded_view_model(view_model)
