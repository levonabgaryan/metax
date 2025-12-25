from typing import Union

from backend.core.application.patterns.use_case_abc import GenericResponseDTO, EmptyResponseDTO
from backend.core.application.use_cases.category.dtos import CategoryBaseResponse
from backend.interface_adapters.patterns.empty_view_model import EmptyViewModel
from backend.interface_adapters.ports.presenters.base_presenter import BasePresenter
from backend.interface_adapters.view_models.category import CategoryBaseViewModel


CategoryViewModel = Union[CategoryBaseViewModel, EmptyViewModel]
CategoryResponse = Union[CategoryBaseResponse, EmptyResponseDTO]


class RestCategoryPresenter(BasePresenter[CategoryViewModel, CategoryResponse]):
    def present(self, response: GenericResponseDTO | None = None) -> CategoryViewModel:
        match response:
            case CategoryBaseResponse():
                return CategoryBaseViewModel(
                    category_uuid=str(response.category_uuid),
                    name=response.name,
                    helper_words=list(response.helper_words),
                )
            case EmptyResponseDTO() | None:
                return EmptyViewModel()
            case _:
                raise TypeError(
                    f"Unexpected response type: {type(response).__name__}. "
                    f"Expected one of: CategoryBaseResponse, EmptyResponseDTO, or None."
                )
