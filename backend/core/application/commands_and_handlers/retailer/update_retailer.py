from dataclasses import dataclass
from uuid import UUID

from backend.core.application.patterns.command import Command
from backend.core.application.patterns.command_handler_abc import CommandHandler


@dataclass(frozen=True)
class UpdateRetailerCommand(Command):
    retailer_uuid: UUID
    retailer_name: str | None
    retailer_url: str | None
    retailer_phone_number: str | None


class UpdateRetailerCommandHandler(CommandHandler[UpdateRetailerCommand]):
    async def handle(self, command: UpdateRetailerCommand) -> None:
        async with self.unit_of_work as uow:
            repo = uow.repositories.retailers
            retailer = await repo.get_by_uuid(command.retailer_uuid)
            new_data = {}
            for key, value in command.__dict__.items():
                if value is not None:
                    new_data.update({key: value})
            retailer.update(new_data)
            await repo.update(updated_retailer=retailer)
            await uow.commit()
