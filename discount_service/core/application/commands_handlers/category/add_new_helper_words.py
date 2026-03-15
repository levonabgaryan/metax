from dataclasses import dataclass
from typing import override
from uuid import UUID
import logging

from discount_service.core.application.commands_handlers.base_command_handler import CommandHandler
from discount_service.core.application.commands_handlers.command import Command


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AddNewHelperWordsCommand(Command):
    category_uuid: UUID
    new_helper_words: frozenset[str]


class AddNewHelperWordsCommandHandler(CommandHandler[AddNewHelperWordsCommand]):
    @override
    async def handle_command(self, command: AddNewHelperWordsCommand) -> None:
        async with self._unit_of_work as uow:
            category_uuid = command.category_uuid
            words_count = len(command.new_helper_words)
            logger.info(
                "COMMAND HANDLING: [AddNewHelperWords] | Category: [%s] | Words Count: %s",
                category_uuid,
                words_count,
            )
            logger.debug(
                "COMMAND DETAILS: [AddNewHelperWords] | Category: [%s] | Words: %s",
                category_uuid,
                list(command.new_helper_words),
            )
            repo = uow.category_repo
            category = await repo.get_by_uuid(command.category_uuid)
            category.add_new_helper_words(command.new_helper_words)
            await repo.update_helper_words(updated_category=category)
            await uow.commit()
        logger.info("COMMAND SUCCESS: [AddNewHelperWords] for Category [%s]", category_uuid)
