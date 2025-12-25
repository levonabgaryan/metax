from typing import Union

from backend.core.application.patterns.use_case_abc import GenericResponseDTO, EmptyResponseDTO
from backend.core.application.use_cases.retailer.dtos import RetailerBaseResponse
from backend.interface_adapters.patterns.empty_view_model import EmptyViewModel
from backend.interface_adapters.ports.presenters.base_presenter import BasePresenter
from backend.interface_adapters.view_models.retailer import RetailerBaseViewModel


RetailerViewModel = Union[RetailerBaseViewModel, EmptyViewModel]
RetailerResponse = Union[RetailerBaseResponse, EmptyResponseDTO]


class RestRetailerPresenter(BasePresenter[RetailerViewModel, RetailerResponse]):
    def present(self, response: GenericResponseDTO | None = None) -> RetailerViewModel:
        match response:
            case RetailerBaseResponse():
                return RetailerBaseViewModel(
                    retailer_uuid=str(response.retailer_uuid),
                    name=response.name,
                    url=response.url,
                    phone_number=response.phone_number,
                )
            case EmptyResponseDTO() | None:
                return EmptyViewModel()
            case _:
                raise TypeError(
                    f"Unexpected response type: {type(response).__name__}. "
                    f"Expected one of: RetailerBaseResponse, EmptyResponseDTO, or None."
                )
