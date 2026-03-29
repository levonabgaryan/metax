from dataclasses import dataclass
from typing import override
from uuid import UUID
import logging

from metax.core.application.commands_handlers.base_command_handler import CommandHandler
from metax.core.application.commands_handlers.command import Command
from metax.core.domain.entities.retailer.entity import Retailer
from metax.core.domain.entities.retailer.value_objects import RetailersNames


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CreateRetailerCommand(Command):
    retailer_uuid: UUID
    name: str
    url: str
    phone_number: str


class CreateRetailerCommandHandler(CommandHandler[CreateRetailerCommand]):
    @override
    async def handle_command(self, command: CreateRetailerCommand) -> None:
        logger.info(
            "[Command: %s] | Status: STARTED | Target UUID: [%s]",
            command.__class__.__name__,
            command.retailer_uuid,
        )
        uow = await self._unit_of_work_provider.create()
        async with uow:
            retailer = Retailer(
                retailer_uuid=command.retailer_uuid,
                name=RetailersNames(command.name),
                phone_number=command.phone_number,
                home_page_url=command.url,
            )
            await uow.retailer_repo.add(retailer)
            await uow.commit()
        logger.info(
            "[Command: %s] | Status: SUCCESS | Target UUID: [%s]",
            command.__class__.__name__,
            retailer.get_uuid(),
        )
