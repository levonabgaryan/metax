from typing import Union

from backend.core.application.patterns.use_case_abc import GenericResponseDTO, EmptyResponseDTO
from backend.core.application.use_cases.retailer.dtos import RetailerEntityDTO
from backend.frameworks_and_drivers.presenters.pydantic_presenters.retailer_presenter_and_schemas.schemas import (
    RetailerEntityViewModelSchema,
)
from backend.interface_adapters.patterns.empty_view_model import EmptyViewModel
from backend.interface_adapters.ports.presenters.base_presenter import BasePresenter
from backend.interface_adapters.view_models.retailer import RetailerEntityViewModel


RetailerViewModel = Union[RetailerEntityViewModel, EmptyViewModel]
RetailerResponseDTO = Union[RetailerEntityDTO, EmptyResponseDTO]


class PydanticRestRetailerPresenter(BasePresenter[RetailerResponseDTO, RetailerViewModel]):
    def present(self, response: GenericResponseDTO | None = None) -> RetailerViewModel:
        match response:
            case RetailerEntityDTO():
                view_model: RetailerViewModel = RetailerEntityViewModelSchema.to_view_model(response)
                return view_model
            case EmptyResponseDTO() | None:
                return EmptyViewModel()
            case _:
                raise TypeError(
                    f"Unexpected response type: {type(response).__name__}. "
                    f"Expected one of: {RetailerEntityDTO.__name__}, {EmptyResponseDTO.__name__}, or None."
                )
