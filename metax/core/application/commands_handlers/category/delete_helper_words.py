import logging
from dataclasses import dataclass
from typing import override
from uuid import UUID

from metax.core.application.commands_handlers.base_command_handler import CommandHandler
from metax.core.application.commands_handlers.command import Command
from metax.core.domain.ddd_patterns.general_value_objects import UUIDValueObject

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DeleteHelperWordsCommand(Command):
    category_uuid: UUID
    words_to_delete: frozenset[str]


class DeleteHelperWordsCommandHandler(CommandHandler[DeleteHelperWordsCommand]):
    @override
    async def handle_command(self, command: DeleteHelperWordsCommand) -> None:
        logger.info(
            "[Command: %s] | Status: STARTED | Target UUID: [%s]",
            command.__class__.__name__,
            command.category_uuid,
        )
        uow = await self._unit_of_work_provider.provide()
        async with uow:
            repo = uow.category_repo
            category = await repo.get_by_uuid(UUIDValueObject.create(command.category_uuid))
            category.delete_helper_words(command.words_to_delete)
            await repo.update(updated_category=category)
            await uow.commit()
        logger.info(
            "[Command: %s] | Status: SUCCESS | Target UUID: [%s]",
            command.__class__.__name__,
            category.get_uuid(),
        )
