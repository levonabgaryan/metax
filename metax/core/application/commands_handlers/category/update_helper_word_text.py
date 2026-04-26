import logging
from dataclasses import dataclass
from typing import override
from uuid import UUID

from metax.core.application.commands_handlers.base_command_handler import CommandHandler
from metax.core.application.commands_handlers.command import Command

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UpdateHelperWordTextCommand(Command):
    category_uuid: UUID
    helper_word_uuid: UUID
    new_text: str


class UpdateHelperWordTextCommandHandler(CommandHandler[UpdateHelperWordTextCommand]):
    @override
    async def handle_command(self, command: UpdateHelperWordTextCommand) -> None:
        logger.info(
            "[Command: %s] | Status: STARTED | Target UUID: [%s]",
            command.__class__.__name__,
            command.category_uuid,
        )
        uow = await self._unit_of_work_provider.provide()
        async with uow:
            repo = uow.category_repo
            category = await repo.get_by_uuid(command.category_uuid)
            category.update_helper_word_text_by_uuid(
                helper_word_uuid=command.helper_word_uuid,
                text=command.new_text,
            )
            await repo.update(updated_category=category)
            await uow.commit()
        logger.info(
            "[Command: %s] | Status: SUCCESS | Target UUID: [%s]",
            command.__class__.__name__,
            category.get_uuid(),
        )
