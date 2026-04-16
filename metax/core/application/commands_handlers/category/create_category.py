import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import override
from uuid import UUID

from metax.core.application.commands_handlers.base_command_handler import CommandHandler
from metax.core.application.commands_handlers.command import Command
from metax.core.domain.entities.category.entity import Category

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CreateCategoryCommand(Command):
    category_uuid: UUID
    name: str
    helper_words: frozenset[str]


class CreateCategoryCommandHandler(CommandHandler[CreateCategoryCommand]):
    @override
    async def handle_command(self, command: CreateCategoryCommand) -> None:
        uow = await self._unit_of_work_provider.provide()
        async with uow:
            logger.info(
                "[Command: %s] | Status: STARTED | Target UUID: [%s]",
                command.__class__.__name__,
                command.category_uuid,
            )
            now = datetime.now(tz=timezone.utc)
            category = Category(
                uuid_=command.category_uuid,
                name=command.name,
                helper_words=command.helper_words,
                created_at=now,
                updated_at=now,
            )
            repo = uow.category_repo
            await repo.add(category)
            await uow.commit()
        logger.info(
            "[Command: %s] | Status: SUCCESS | Target UUID: [%s]",
            command.__class__.__name__,
            category.get_uuid(),
        )
