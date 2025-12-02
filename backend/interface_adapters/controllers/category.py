from uuid import uuid4

from backend.core.application.patterns.empty_dto import EmptyResponse
from backend.core.application.patterns.result_type import Error, Result
from backend.core.application.use_cases.category.add_new_category_helper_words import (
    AddNewCategoryHelperWordsUseCase,
)
from backend.core.application.use_cases.category.create_category import CreateCategoryUseCase
from backend.core.application.use_cases.category.delete_helper_words import DeleteCategoryHelperWordsUseCase
from backend.core.application.use_cases.category.dtos import (
    AddNewCategoryHelperWordsRequest,
    CreateCategoryRequest,
    CreateCategoryResponse,
    DeleteCategoryHelperWordsRequest,
)
from backend.interface_adapters.error_view_model import ErrorViewModel
from backend.interface_adapters.presenters.ports.category.add_new_helper_words_presenter import (
    AddNewCategoryHelperWordsViewModel,
    IAddNewCategoryHelperWordsPresenter,
)
from backend.interface_adapters.presenters.ports.category.create_category_presenter import (
    CreateCategoryViewModel,
    ICreateCategoryPresenter,
)
from backend.interface_adapters.presenters.ports.category.delete_helper_words_presenter import (
    DeleteCategoryHelperWordsViewModel,
    IDeleteCategoryHelperWordsPresenter,
)


class CategoryController:
    def __init__(
        self,
        create_category_use_case: CreateCategoryUseCase,
        add_new_helper_words_use_case: AddNewCategoryHelperWordsUseCase,
        delete_helper_words_use_case: DeleteCategoryHelperWordsUseCase,
    ) -> None:
        self.create_category_use_case = create_category_use_case
        self.add_new_helper_words_use_case = add_new_helper_words_use_case
        self.delete_helper_words_use_case = delete_helper_words_use_case

    async def create(
        self,
        create_category_presenter: ICreateCategoryPresenter[CreateCategoryViewModel],
        name: str,
        helper_words: frozenset[str],
    ) -> CreateCategoryViewModel | ErrorViewModel:
        request = CreateCategoryRequest(category_uuid=uuid4(), name=name, helper_words=helper_words)
        result: Result[CreateCategoryResponse] = await self.create_category_use_case.execute(request)

        if result.is_succeed:
            success_response: CreateCategoryResponse = result.get_success_value()
            return create_category_presenter.present_view_model(success_response)

        error_response: Error = result.get_error_value()
        return create_category_presenter.present_error_view_model(error_response)

    async def add_new_helper_words(
        self,
        presenter: IAddNewCategoryHelperWordsPresenter[AddNewCategoryHelperWordsViewModel],
        category_name: str,
        new_words: set[str],
    ) -> AddNewCategoryHelperWordsViewModel | ErrorViewModel:
        request = AddNewCategoryHelperWordsRequest(
            category_name=category_name, new_helper_words=frozenset(new_words)
        )
        result: Result[EmptyResponse] = await self.add_new_helper_words_use_case.execute(request)

        if result.is_succeed:
            success_response: EmptyResponse = result.get_success_value()
            return presenter.present_view_model(success_response)

        error_response: Error = result.get_error_value()
        return presenter.present_error_view_model(error_response)

    async def delete_helper_words(
        self,
        presenter: IDeleteCategoryHelperWordsPresenter[DeleteCategoryHelperWordsViewModel],
        category_name: str,
        words_to_delete: set[str],
    ) -> DeleteCategoryHelperWordsViewModel | ErrorViewModel:
        request = DeleteCategoryHelperWordsRequest(category_name, frozenset(words_to_delete))
        result: Result[EmptyResponse] = await self.delete_helper_words_use_case.execute(request)
        if result.is_failure:
            return presenter.present_error_view_model(result.get_error_value())
        return presenter.present_view_model(result.get_success_value())
