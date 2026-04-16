import logging
from dataclasses import dataclass, field
from typing import override
from uuid import UUID

from metax.core.application.commands_handlers.base_command_handler import CommandHandler
from metax.core.application.commands_handlers.command import Command
from metax.core.application.event_handlers.retailer.events import RetailerUpdated
from metax.core.domain.ddd_patterns.general_value_objects import UUIDValueObject
from metax.core.domain.entities.retailer.value_objects import RetailersNames

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UpdateRetailerCommand(Command):
    retailer_uuid: UUID
    new_name: str | None = field(default=None)
    new_url: str | None = field(default=None)
    new_phone_number: str | None = field(default=None)


class UpdateRetailerCommandHandler(CommandHandler[UpdateRetailerCommand]):
    @override
    async def handle_command(self, command: UpdateRetailerCommand) -> None:
        logger.info(
            "[Command: %s] | Status: STARTED | Target UUID: [%s]",
            command.__class__.__name__,
            command.retailer_uuid,
        )
        uow = await self._unit_of_work_provider.provide()
        async with uow:
            repo = uow.retailer_repo
            retailer = await repo.get_by_uuid(UUIDValueObject.create(command.retailer_uuid))
            if command.new_name is not None:
                retailer.set_name(RetailersNames(command.new_name))
            if command.new_url is not None:
                retailer.set_home_page_url(command.new_url)
            if command.new_phone_number is not None:
                retailer.set_phone_number(command.new_phone_number)

            await repo.update(updated_retailer=retailer)
            await uow.commit()
        logger.info(
            "[Command: %s] | Status: SUCCESS | Target UUID: [%s]",
            command.__class__.__name__,
            retailer.get_uuid(),
        )
        event = RetailerUpdated(retailer_uuid=retailer.get_uuid())
        await self._event_bus.handle(event)
