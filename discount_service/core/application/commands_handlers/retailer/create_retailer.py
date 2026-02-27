from dataclasses import dataclass
from uuid import UUID

from discount_service.core.application.commands_handlers.base_command_handler import CommandHandler
from discount_service.core.application.commands_handlers.command import Command
from discount_service.core.domain.entities.retailer_entity.retailer import Retailer


@dataclass(frozen=True)
class CreateRetailerCommand(Command):
    retailer_uuid: UUID
    name: str
    url: str
    phone_number: str


class CreateRetailerCommandHandler(CommandHandler[CreateRetailerCommand]):
    async def handle_command(self, command: CreateRetailerCommand) -> None:
        async with self._unit_of_work as uow:
            retailer = Retailer(
                retailer_uuid=command.retailer_uuid,
                name=command.name,
                phone_number=command.phone_number,
                home_page_url=command.url,
            )
            await uow.retailer_repo.add(retailer)
            await uow.commit()
