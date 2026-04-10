import logging
from dataclasses import dataclass
from typing import override
from uuid import UUID

from metax.core.application.commands_handlers.base_command_handler import CommandHandler
from metax.core.application.commands_handlers.command import Command

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AddNewHelperWordsCommand(Command):
    category_uuid: UUID
    new_helper_words: frozenset[str]


class AddNewHelperWordsCommandHandler(CommandHandler[AddNewHelperWordsCommand]):
    @override
    async def handle_command(self, command: AddNewHelperWordsCommand) -> None:
        logger.info(
            "[Command: %s] | Status: STARTED | Target UUID: [%s]",
            command.__class__.__name__,
            command.category_uuid,
        )
        uow = await self._unit_of_work_provider.create()
        async with uow:
            repo = uow.category_repo
            category = await repo.get_by_uuid(command.category_uuid)
            category.add_new_helper_words(command.new_helper_words)
            await repo.update_helper_words(updated_category=category)
            await uow.commit()
        logger.info(
            "[Command: %s] | Status: SUCCESS | Target UUID: [%s]",
            command.__class__.__name__,
            category.get_uuid(),
        )
