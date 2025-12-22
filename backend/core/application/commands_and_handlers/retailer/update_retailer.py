from dataclasses import dataclass
from typing import Any
from uuid import UUID

from backend.core.application.patterns.command import Command
from backend.core.application.patterns.command_handler_abc import CommandHandler
from backend.core.application.ports.repositories.retailer import RetailerFieldsToUpdate


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
    def new_data(self) -> dict[str, Any]:
        new_data = {}
        for key, value in self.__dict__.items():
            if value is not None:
                new_data.update({key: value})
        return new_data


class UpdateRetailerCommandHandler(CommandHandler[UpdateRetailerCommand]):
    async def handle(self, command: UpdateRetailerCommand) -> None:
        async with self.unit_of_work as uow:
            repo = uow.repositories.retailer
            retailer = await repo.get_by_uuid(command.retailer_uuid)
            new_data = command.new_data
            retailer.update(new_data)
            await repo.update(updated_retailer=retailer, fields_to_update=command.fields_to_update)
            await uow.commit()
