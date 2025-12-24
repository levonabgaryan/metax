from uuid import UUID, uuid4

from backend.core.application.commands_and_handlers.category import (
    CreateCategoryCommand,
    CreateCategoryCommandHandler,
)
from backend.core.application.patterns.message_buss import MessageBus
from backend.core.application.patterns.use_case_abc import EmptyResponseDTO, GenericResponseDTO
from backend.core.application.input_ports.repositories.errors.errors import EntityIsNotFoundError
from backend.core.application.use_cases.category.add_new_category_helper_words import AddHelperWordsUseCase
from backend.core.application.use_cases.category.delete_helper_words import DeleteHelperWordsUseCase
from backend.core.application.use_cases.category.dtos import AddHelperWordsRequest, DeleteHelperWordsRequest
from backend.core.domain.entities.category_entity.errors.errors import (
    CategoryHelperWordsNotFoundForDeletionError,
    DuplicateCategoryHelperWordsError,
)
from backend.interface_adapters.patterns.empty_view_model import EmptyViewModel
from backend.interface_adapters.patterns.operation_result import OperationResult
from backend.interface_adapters.output_ports.presenters.base_presenter import BasePresenter
from backend.interface_adapters.view_models.category import CategoryBaseViewModel


class CategoryController:
    def __init__(
        self,
        message_bus: MessageBus,
        create_category_cmd_handler: CreateCategoryCommandHandler,
        add_new_helper_words_use_case: AddHelperWordsUseCase,
        delete_helper_words_use_case: DeleteHelperWordsUseCase,
        category_presenter: BasePresenter[CategoryBaseViewModel, GenericResponseDTO],
    ) -> None:
        self.message_bus = message_bus
        self.create_category_cmd_handler = create_category_cmd_handler
        self.add_new_helper_words_use_case = add_new_helper_words_use_case
        self.delete_helper_words_use_case = delete_helper_words_use_case
        self.category_presenter = category_presenter

    async def create(
        self,
        name: str,
        helper_words: frozenset[str],
    ) -> OperationResult[EmptyViewModel]:
        command = CreateCategoryCommand(name=name, helper_words=helper_words, category_uuid=uuid4())
        await self.message_bus.handle(command)
        view_model = self.category_presenter.present_empty(EmptyResponseDTO())
        return OperationResult.from_succeeded_view_model(view_model)

    async def add_new_helper_words(
        self,
        category_uuid: UUID,
        new_words: frozenset[str],
    ) -> OperationResult[EmptyViewModel]:
        request = AddHelperWordsRequest(category_uuid=category_uuid, new_helper_words=new_words)
        try:
            response = await self.add_new_helper_words_use_case.execute(request)
        except DuplicateCategoryHelperWordsError as error:
            error_view_model = self.category_presenter.present_error(
                message=error.message,
                error_code=error.error_code,
                details=error.details,
            )
            return OperationResult.from_error_view_model(error_view_model)
        except EntityIsNotFoundError as error:
            error_view_model = self.category_presenter.present_error(
                message=error.message,
                error_code=error.error_code,
                details=error.details,
            )
            return OperationResult.from_error_view_model(error_view_model)

        view_model = self.category_presenter.present_empty(response)
        return OperationResult.from_succeeded_view_model(view_model)

    async def delete_helper_words(
        self,
        category_uuid: UUID,
        words_to_delete: frozenset[str],
    ) -> OperationResult[EmptyViewModel]:
        request = DeleteHelperWordsRequest(category_uuid=category_uuid, words_to_delete=words_to_delete)
        try:
            response = await self.delete_helper_words_use_case.execute(request)
        except CategoryHelperWordsNotFoundForDeletionError as error:
            error_view_model = self.category_presenter.present_error(
                message=error.message,
                error_code=error.error_code,
                details=error.details,
            )
            return OperationResult.from_error_view_model(error_view_model)
        except EntityIsNotFoundError as error:
            error_view_model = self.category_presenter.present_error(
                message=error.message,
                error_code=error.error_code,
                details=error.details,
            )
            return OperationResult.from_error_view_model(error_view_model)

        view_model = self.category_presenter.present_empty(response)
        return OperationResult.from_succeeded_view_model(view_model)
