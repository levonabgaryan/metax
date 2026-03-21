from dataclasses import dataclass, field
from typing import override
from uuid import UUID
import logging

from metax.core.application.event_handlers.category.events import CategoryUpdated
from metax.core.application.commands_handlers.base_command_handler import CommandHandler
from metax.core.application.commands_handlers.command import Command
from metax.core.application.ports.repositories.entites_repositories.category import (
    CategoryFieldsToUpdate,
)
from metax.core.domain.entities.category_entity.category import DataForCategoryUpdate


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UpdateCategoryCommand(Command):
    category_uuid: UUID
    new_name: str | None = field(default=None)

    @property
    def fields_to_update(self) -> CategoryFieldsToUpdate:
        return CategoryFieldsToUpdate(name=self.new_name is not None)

    @property
    def new_data(self) -> DataForCategoryUpdate:
        return DataForCategoryUpdate(new_name=self.new_name)


class UpdateCategoryCommandHandler(CommandHandler[UpdateCategoryCommand]):
    @override
    async def handle_command(self, command: UpdateCategoryCommand) -> None:
        logger.info(
            "[Command: %s] | Status: STARTED | Target UUID: [%s]",
            command.__class__.__name__,
            command.category_uuid,
        )
        async with self._unit_of_work as uow:
            repo = uow.category_repo
            category = await repo.get_by_uuid(command.category_uuid)
            new_data = command.new_data
            category.update(new_data)
            await repo.update(updated_category=category, fields_to_update=command.fields_to_update)
            await uow.commit()
        logger.info(
            "[Command: %s] | Status: SUCCESS | Target UUID: [%s]",
            command.__class__.__name__,
            category.get_uuid(),
        )
        event = CategoryUpdated(category_uuid=category.get_uuid())
        await self._event_bus.handle(event)
