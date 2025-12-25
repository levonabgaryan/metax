from typing import Union

from backend.core.application.patterns.use_case_abc import GenericResponseDTO, EmptyResponseDTO
from backend.core.application.use_cases.discounted_product.dtos import DiscountedEntityBaseResponse
from backend.frameworks_and_drivers.presenters.pydantic_presenters.discounted_product_presenter_and_schemas.schemas import (
    DiscountedProductEntityViewModelSchema,
)
from backend.interface_adapters.patterns.empty_view_model import EmptyViewModel
from backend.interface_adapters.ports.presenters.base_presenter import BasePresenter
from backend.interface_adapters.view_models.discounted_product import DiscountedProductEntityViewModel

DiscountedProductResponse = Union[DiscountedEntityBaseResponse, EmptyResponseDTO]
DiscountedProductViewModel = Union[DiscountedProductEntityViewModel, EmptyViewModel]


class RestDiscountedProductPresenter(BasePresenter[DiscountedProductViewModel, DiscountedProductResponse]):
    def present(self, response: GenericResponseDTO | None = None) -> DiscountedProductViewModel:
        match response:
            case DiscountedEntityBaseResponse():
                view_model = DiscountedProductEntityViewModelSchema.to_view_model(response)
                return view_model
            case EmptyResponseDTO() | None:
                return EmptyViewModel()
            case _:
                raise TypeError(
                    f"Unexpected response type: {type(response).__name__}. "
                    f"Expected one of: DiscountedProductBaseResponse, EmptyResponseDTO, or None."
                )
