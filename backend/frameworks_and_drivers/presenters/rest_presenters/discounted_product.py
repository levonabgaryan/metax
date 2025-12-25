from typing import Union

from backend.core.application.patterns.use_case_abc import GenericResponseDTO, EmptyResponseDTO
from backend.core.application.use_cases.discounted_product.dtos import DiscountedProductBaseResponse
from backend.interface_adapters.patterns.empty_view_model import EmptyViewModel
from backend.interface_adapters.ports.presenters.base_presenter import BasePresenter
from backend.interface_adapters.view_models.discounted_product import DiscountedProductBaseViewModel

DiscountedProductResponse = Union[DiscountedProductBaseResponse, EmptyResponseDTO]
DiscountedProductViewModel = Union[DiscountedProductBaseViewModel, EmptyViewModel]


class RestDiscountedProductPresenter(BasePresenter[DiscountedProductViewModel, DiscountedProductResponse]):
    def present(self, response: GenericResponseDTO | None = None) -> DiscountedProductViewModel:
        match response:
            case DiscountedProductBaseResponse():
                return DiscountedProductBaseViewModel(
                    discounted_product_uuid=str(response.discounted_product_uuid),
                    discounted_price=str(response.price_details.discounted_price),
                    real_price=str(response.price_details.real_price),
                    name=str(response.name),
                    url=str(response.url),
                    retailer_name=str(response.retailer_name),
                    category_name=str(response.category_name),
                )
            case EmptyResponseDTO() | None:
                return EmptyViewModel()
            case _:
                raise TypeError(
                    f"Unexpected response type: {type(response).__name__}. "
                    f"Expected one of: DiscountedProductBaseResponse, EmptyResponseDTO, or None."
                )
