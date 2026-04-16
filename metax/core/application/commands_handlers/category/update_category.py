import logging
from dataclasses import dataclass, field
from typing import override
from uuid import UUID

from metax.core.application.commands_handlers.base_command_handler import CommandHandler
from metax.core.application.commands_handlers.command import Command
from metax.core.application.event_handlers.category.events import CategoryUpdated
from metax.core.domain.ddd_patterns.general_value_objects import UUIDValueObject

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UpdateCategoryCommand(Command):
    category_uuid: UUID
    new_name: str | None = field(default=None)


class UpdateCategoryCommandHandler(CommandHandler[UpdateCategoryCommand]):
    @override
    async def handle_command(self, command: UpdateCategoryCommand) -> None:
        logger.info(
            "[Command: %s] | Status: STARTED | Target UUID: [%s]",
            command.__class__.__name__,
            command.category_uuid,
        )
        uow = await self._unit_of_work_provider.provide()
        async with uow:
            repo = uow.category_repo
            category = await repo.get_by_uuid(UUIDValueObject.create(command.category_uuid))
            if command.new_name is not None:
                category.set_name(command.new_name)

            await repo.update(updated_category=category)
            await uow.commit()
        logger.info(
            "[Command: %s] | Status: SUCCESS | Target UUID: [%s]",
            command.__class__.__name__,
            category.get_uuid(),
        )
        event = CategoryUpdated(category_uuid=category.get_uuid())
        await self._event_bus.handle(event)
