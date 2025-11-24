from uuid import uuid4

from app.core.application.patterns.result_type import Result
from app.core.application.use_cases.category.create_category import CreateCategoryUseCase
from app.core.application.use_cases.category.dtos import CreateCategoryRequest, CreateCategoryResponse
from app.interface_adapters.error_view_model import ErrorViewModel
from app.interface_adapters.presenters.ports.category.create_category_presenter import (
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
        response: Result[CreateCategoryResponse] = await self.create_category_use_case.execute(request)
        return create_category_presenter.present(response)
