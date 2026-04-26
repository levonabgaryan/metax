import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

from metax.core.application.commands_handlers.base_command_handler import CommandHandler
from metax.core.application.commands_handlers.command import Command
from metax.core.domain.entities.category_helper_word.entity import CategoryHelperWord

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HelperWordPayload:
    text: str


@dataclass(frozen=True)
class AddNewHelperWordsCommand(Command):
    category_uuid: UUID
    new_helper_words: list[HelperWordPayload]


class AddNewHelperWordsCommandHandler(CommandHandler[AddNewHelperWordsCommand]):
    @override
    async def handle_command(self, command: AddNewHelperWordsCommand) -> None:
        logger.info(
            "[Command: %s] | Status: STARTED | Target UUID: [%s]",
            command.__class__.__name__,
            command.category_uuid,
        )
        now = datetime.now(tz=UTC)

        uow = await self._unit_of_work_provider.provide()
        async with uow:
            repo = uow.category_repo
            category = await repo.get_by_uuid(command.category_uuid)
            new_helper_words_entities = [
                CategoryHelperWord(
                    uuid_=uuid.uuid7(),
                    created_at=now,
                    updated_at=now,
                    text=helper_word.text,
                )
                for helper_word in command.new_helper_words
            ]
            category.add_new_helper_words(new_helper_words_entities)
            await repo.update(updated_category=category)
            await uow.commit()
        logger.info(
            "[Command: %s] | Status: SUCCESS | Target UUID: [%s]",
            command.__class__.__name__,
            category.get_uuid(),
        )
