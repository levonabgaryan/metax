from typing import Union

from backend.core.application.patterns.use_case_abc import GenericResponseDTO, EmptyResponseDTO
from backend.core.application.use_cases.category.dtos import CategoryEntityDTO
from backend.frameworks_and_drivers.presenters.pydantic_presenters.category_presenter_and_schemas.schemas import (
    CategoryEntityViewModelSchema,
)
from backend.interface_adapters.patterns.empty_view_model import EmptyViewModel
from backend.interface_adapters.ports.presenters.base_presenter import BasePresenter
from backend.interface_adapters.view_models.category import CategoryEntityViewModel


CategoryViewModel = Union[CategoryEntityViewModel, EmptyViewModel]
CategoryResponse = Union[CategoryEntityDTO, EmptyResponseDTO]


class RestCategoryPresenter(BasePresenter[CategoryViewModel, CategoryResponse]):
    def present(self, response: GenericResponseDTO | None = None) -> CategoryViewModel:
        match response:
            case CategoryEntityDTO():
                view_model: CategoryEntityViewModel = CategoryEntityViewModelSchema.to_view_model(response)
                return view_model
            case EmptyResponseDTO() | None:
                return EmptyViewModel()
            case _:
                raise TypeError(
                    f"Unexpected response type: {type(response).__name__}. "
                    f"Expected one of: {CategoryEntityDTO.__name__}, {EmptyResponseDTO.__name__}, or None."
                )
