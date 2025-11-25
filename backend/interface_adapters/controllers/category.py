from uuid import uuid4

from backend.core.application.patterns.result_type import Error, Result
from backend.core.application.use_cases.category.create_category import CreateCategoryUseCase
from backend.core.application.use_cases.category.dtos import CreateCategoryRequest, CreateCategoryResponse
from backend.interface_adapters.error_view_model import ErrorViewModel
from backend.interface_adapters.presenters.ports.category.create_category_presenter import (
    CreateCategoryViewModel,
    ICreateCategoryPresenter,
)


class CategoryController:
    def __init__(self, create_category_use_case: CreateCategoryUseCase) -> None:
        self.create_category_use_case = create_category_use_case

    async def handle_create(
        self,
        create_category_presenter: ICreateCategoryPresenter[CreateCategoryViewModel],
        name: str,
        helper_words: list[str],
    ) -> CreateCategoryViewModel | ErrorViewModel:
        request = CreateCategoryRequest(category_uuid=uuid4(), name=name, helper_words=frozenset(helper_words))
        result: Result[CreateCategoryResponse] = await self.create_category_use_case.execute(request)

        if result.is_succeed:
            success_response: CreateCategoryResponse = result.get_success_value()
            return create_category_presenter.present_view_model(success_response)

        error_response: Error = result.get_error_value()
        return create_category_presenter.present_error(error_response)
