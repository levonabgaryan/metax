from dataclasses import dataclass, field
from uuid import UUID

from discount_service.core.application.patterns.command import Command
from discount_service.core.application.patterns.command_handler_abc import CommandHandler
from discount_service.core.application.ports.repositories.entites_repositories.category import (
    CategoryFieldsToUpdate,
)
from discount_service.core.domain.entities.category_entity.category import DataForCategoryUpdate


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
    async def handle(self, command: UpdateCategoryCommand) -> None:
        async with self.unit_of_work as uow:
            repo = uow.category_repo
            category = await repo.get_by_uuid(command.category_uuid)
            new_data = command.new_data
            category.update(new_data)
            await repo.update(updated_category=category, fields_to_update=command.fields_to_update)
            await uow.commit()
