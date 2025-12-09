from dataclasses import dataclass
from uuid import UUID

from backend.core.application.patterns.command import Command
from backend.core.application.patterns.command_handler_abc import CommandHandler


@dataclass(frozen=True)
class UpdateCategoryNameCommand(Command):
    category_uuid: UUID
    new_name: str


class UpdateCategoryNameCommandHandler(CommandHandler[UpdateCategoryNameCommand]):
    async def handle(self, command: UpdateCategoryNameCommand) -> None:
        async with self.unit_of_work as uow:
            repo = uow.repositories.categories
            category = await repo.get_by_uuid(command.category_uuid)
            category.set_name(new_name=command.new_name)
            await repo.update(updated_category=category)
            await uow.commit()
