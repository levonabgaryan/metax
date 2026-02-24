from dataclasses import dataclass
from uuid import UUID

from discount_service.core.application.patterns.command import Command
from discount_service.core.application.patterns.command_handler_abc import CommandHandler
from discount_service.core.domain.entities.category_entity.category import Category, CategoryHelperWords


@dataclass(frozen=True)
class CreateCategoryCommand(Command):
    category_uuid: UUID
    name: str
    helper_words: frozenset[str]


class CreateCategoryCommandHandler(CommandHandler[CreateCategoryCommand]):
    async def handle(self, command: CreateCategoryCommand) -> None:
        async with self.__unit_of_work as uow:
            helper_words = CategoryHelperWords(command.helper_words)
            category = Category(category_uuid=command.category_uuid, name=command.name, helper_words=helper_words)
            repo = uow.category_repo
            await repo.add(category)
            await uow.commit()
