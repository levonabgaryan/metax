from dataclasses import dataclass
from uuid import UUID

from discount_service.core.application.patterns.command import Command
from discount_service.core.application.patterns.command_handler_abc import CommandHandler
from discount_service.core.domain.entities.retailer_entity.retailer import Retailer


@dataclass(frozen=True)
class CreateRetailerCommand(Command):
    retailer_uuid: UUID
    name: str
    url: str
    phone_number: str


class CreateRetailerCommandHandler(CommandHandler[CreateRetailerCommand]):
    async def handle(self, command: CreateRetailerCommand) -> None:
        async with self.unit_of_work as uow:
            retailer = Retailer(
                retailer_uuid=command.retailer_uuid,
                name=command.name,
                phone_number=command.phone_number,
                url=command.url,
            )
            await uow.repositories.retailer.add(retailer)
            await uow.commit()
