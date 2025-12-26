from typing import Union

from backend.core.application.patterns.use_case_abc import GenericResponseDTO, EmptyResponseDTO
from backend.core.application.use_cases.category.dtos import CategoryEntityResponseDTO
from backend.frameworks_and_drivers.presenters.pydantic_presenters.category_presenter_and_schemas.schemas import (
    CategoryEntityViewModelSchema,
)
from backend.interface_adapters.patterns.empty_view_model import EmptyViewModel
from backend.interface_adapters.ports.presenters.base_presenter import BasePresenter
from backend.interface_adapters.view_models.category import CategoryEntityViewModel


CategoryViewModel = Union[CategoryEntityViewModel, EmptyViewModel]
CategoryResponseDTO = Union[CategoryEntityResponseDTO, EmptyResponseDTO]


class PydanticCategoryPresenter(BasePresenter[CategoryResponseDTO, CategoryViewModel]):
    def present(self, response: GenericResponseDTO | None = None) -> CategoryViewModel:
        match response:
            case CategoryEntityResponseDTO():
                view_model: CategoryEntityViewModel = CategoryEntityViewModelSchema.to_view_model(response)
                return view_model
            case EmptyResponseDTO() | None:
                return EmptyViewModel()
            case _:
                raise TypeError(
                    f"Unexpected response type: {type(response).__name__}. "
                    f"Expected one of: {CategoryEntityResponseDTO.__name__}, {EmptyResponseDTO.__name__}, or None."
                )
