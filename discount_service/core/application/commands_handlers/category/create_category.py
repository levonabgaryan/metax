import logging
from dataclasses import dataclass
from typing import override
from uuid import UUID

from discount_service.core.application.commands_handlers.base_command_handler import CommandHandler
from discount_service.core.application.commands_handlers.command import Command
from discount_service.core.domain.entities.category_entity.category import Category, CategoryHelperWords


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CreateCategoryCommand(Command):
    category_uuid: UUID
    name: str
    helper_words: frozenset[str]


class CreateCategoryCommandHandler(CommandHandler[CreateCategoryCommand]):
    @override
    async def handle_command(self, command: CreateCategoryCommand) -> None:
        async with self._unit_of_work as uow:
            logger.info(
                "COMMAND HANDLING: [CreateCategory] | Category [%s]",
                command.category_uuid,
            )
            logger.debug(
                "COMMAND DETAILS: [CreateCategory] | Category [%s] | Name [%s] | HelperWords [%s]",
                command.category_uuid,
                command.name,
                list(command.helper_words),
            )
            helper_words = CategoryHelperWords(command.helper_words)
            category = Category(category_uuid=command.category_uuid, name=command.name, helper_words=helper_words)
            repo = uow.category_repo
            await repo.add(category)
            await uow.commit()
        logger.info("COMMAND SUCCESS: [CreateCategory] for Category [%s]", command.category_uuid)
