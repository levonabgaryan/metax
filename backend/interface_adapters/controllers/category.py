from uuid import UUID, uuid4

from backend.core.application.commands_and_handlers.category import (
    AddHelperWordsCommand,
    AddHelperWordsCommandHandler,
    CreateCategoryCommand,
    CreateCategoryCommandHandler,
    DeleteHelperWordsCommand,
    DeleteHelperWordsCommandHandler,
)
from backend.core.application.patterns.message_buss import MessageBus
from backend.core.application.ports.repositories.errors.errors import EntityIsNotFoundError
from backend.core.domain.entities.category_entity.errors.errors import (
    CategoryHelperWordsNotFoundForDeletionError,
    DuplicateCategoryHelperWordsError,
)
from backend.interface_adapters.empty_view_model import EmptyViewModel
from backend.interface_adapters.error_view_model import ErrorViewModel


class CategoryController:
    def __init__(
        self,
        message_bus: MessageBus,
        create_category_cmd_handler: CreateCategoryCommandHandler,
        add_new_helper_words_cmd_handler: AddHelperWordsCommandHandler,
        delete_helper_words_cmd_handler: DeleteHelperWordsCommandHandler,
    ) -> None:
        self.message_bus = message_bus
        self.create_category_cmd_handler = create_category_cmd_handler
        self.add_new_helper_words_cmd_handler = add_new_helper_words_cmd_handler
        self.delete_helper_words_cmd_handler = delete_helper_words_cmd_handler

    async def create(
        self,
        name: str,
        helper_words: frozenset[str],
    ) -> EmptyViewModel | ErrorViewModel:
        command = CreateCategoryCommand(name=name, helper_words=helper_words, category_uuid=uuid4())
        await self.message_bus.handle(command)
        return EmptyViewModel()

    async def add_new_helper_words(
        self,
        category_uuid: UUID,
        new_words: frozenset[str],
    ) -> EmptyViewModel | ErrorViewModel:
        command = AddHelperWordsCommand(category_uuid=category_uuid, new_helper_words=new_words)
        try:
            await self.message_bus.handle(command)
        except DuplicateCategoryHelperWordsError as error:
            return ErrorViewModel.from_error(error)
        except EntityIsNotFoundError as error:
            return ErrorViewModel.from_error(error)

        return EmptyViewModel()

    async def delete_helper_words(
        self,
        category_uuid: UUID,
        words_to_delete: frozenset[str],
    ) -> EmptyViewModel | ErrorViewModel:
        command = DeleteHelperWordsCommand(category_uuid=category_uuid, words_to_delete=words_to_delete)
        try:
            await self.message_bus.handle(command)
        except CategoryHelperWordsNotFoundForDeletionError as error:
            return ErrorViewModel.from_error(error)
        except EntityIsNotFoundError as error:
            return ErrorViewModel.from_error(error)

        return EmptyViewModel()
