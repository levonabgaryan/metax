from dataclasses import dataclass
from typing import override
from uuid import UUID

from discount_service.core.application.event_handlers.retailer.events import RetailerUpdated
from discount_service.core.application.commands_handlers.base_command_handler import CommandHandler
from discount_service.core.application.commands_handlers.command import Command
from discount_service.core.application.ports.repositories.entites_repositories.retailer import (
    RetailerFieldsToUpdate,
)
from discount_service.core.domain.entities.retailer_entity.retailer import DataForRetailerUpdate


@dataclass(frozen=True)
class UpdateRetailerCommand(Command):
    retailer_uuid: UUID
    new_name: str | None
    new_url: str | None
    new_phone_number: str | None

    @property
    def fields_to_update(self) -> RetailerFieldsToUpdate:
        return RetailerFieldsToUpdate(
            name=self.new_name is not None,
            url=self.new_url is not None,
            phone_number=self.new_phone_number is not None,
        )

    @property
    def new_data(self) -> DataForRetailerUpdate:
        return DataForRetailerUpdate(
            new_name=self.new_name,
            new_url=self.new_url,
            new_phone_number=self.new_phone_number,
        )


class UpdateRetailerCommandHandler(CommandHandler[UpdateRetailerCommand]):
    @override
    async def handle_command(self, command: UpdateRetailerCommand) -> None:
        async with self._unit_of_work as uow:
            repo = uow.retailer_repo
            retailer = await repo.get_by_uuid(command.retailer_uuid)
            new_data = command.new_data
            retailer.update(new_data)
            await repo.update(updated_retailer=retailer, fields_to_update=command.fields_to_update)
            await uow.commit()
        event = RetailerUpdated(retailer_uuid=retailer.get_uuid())
        await self._event_bus.handle(event)
