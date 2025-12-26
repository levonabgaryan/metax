from typing import Union

from backend.core.application.patterns.use_case_abc import GenericResponseDTO, EmptyResponseDTO
from backend.core.application.use_cases.discounted_product.dtos import DiscountedProductEntityResponseDTO
from backend.frameworks_and_drivers.presenters.pydantic_presenters.discounted_product_presenter_and_schemas.schemas import (
    DiscountedProductEntityViewModelSchema,
)
from backend.interface_adapters.patterns.empty_view_model import EmptyViewModel
from backend.interface_adapters.ports.presenters.base_presenter import BasePresenter
from backend.interface_adapters.view_models.discounted_product import DiscountedProductEntityViewModel

DiscountedProductResponseDTO = Union[DiscountedProductEntityResponseDTO, EmptyResponseDTO]
DiscountedProductViewModel = Union[DiscountedProductEntityViewModel, EmptyViewModel]


class PydanticDiscountedProductPresenter(BasePresenter[DiscountedProductResponseDTO, DiscountedProductViewModel]):
    def present(self, response: GenericResponseDTO | None = None) -> DiscountedProductViewModel:
        match response:
            case DiscountedProductEntityResponseDTO():
                view_model: DiscountedProductEntityViewModel = (
                    DiscountedProductEntityViewModelSchema.to_view_model(response)
                )
                return view_model
            case EmptyResponseDTO() | None:
                return EmptyViewModel()
            case _:
                raise TypeError(
                    f"Unexpected response type: {type(response).__name__}. "
                    f"Expected one of: {DiscountedProductEntityResponseDTO.__name__}, {EmptyResponseDTO.__name__}, or None."
                )
