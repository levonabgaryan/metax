from dataclasses import dataclass
from uuid import UUID

from backend.core.application.patterns.command import Command
from backend.core.application.patterns.command_handler_abc import CommandHandler


@dataclass(frozen=True)
class AddHelperWordsCommand(Command):
    category_uuid: UUID
    new_helper_words: frozenset[str]


class AddHelperWordsCommandHandler(CommandHandler[AddHelperWordsCommand]):
    async def handle(self, command: AddHelperWordsCommand) -> None:
        async with self.unit_of_work as uow:
            repo = uow.repositories.categories
            category = await repo.get_by_uuid(command.category_uuid)
            category.add_new_helper_words(command.new_helper_words)
            await repo.update(updated_category=category)
            await uow.commit()
