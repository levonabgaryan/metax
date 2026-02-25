from dataclasses import dataclass
from uuid import UUID

from discount_service.core.application.patterns.command_handler_abc import CommandHandler
from discount_service.core.application.patterns.message_bus_1 import Command


@dataclass(frozen=True)
class DeleteHelperWordsCommand(Command):
    category_uuid: UUID
    words_to_delete: frozenset[str]


class DeleteHelperWordsCommandHandler(CommandHandler):
    async def handle_command(self, command: DeleteHelperWordsCommand) -> None:
        async with self.__unit_of_work as uow:
            repo = uow.category_repo
            category = await repo.get_by_uuid(command.category_uuid)
            category.delete_helper_words(command.words_to_delete)
            await repo.update_helper_words(updated_category=category)
            await uow.commit()
