from uuid import uuid4

from backend.core.application.patterns.result_type import Error, Result
from backend.core.application.use_cases.retailer.create_retailer import CreateRetailerUseCase
from backend.core.application.use_cases.retailer.dtos import CreateRetailerRequest, CreateRetailerResponse
from backend.interface_adapters.error_view_model import ErrorViewModel
from backend.interface_adapters.presenters.ports.retailer.create_retailer_presenter import (
    CreateRetailerViewModel,
    ICreateRetailerPresenter,
)


class RetailerController:
    def __init__(self, create_retailer_use_case: CreateRetailerUseCase) -> None:
        self.create_retailer_use_case = create_retailer_use_case

    async def create(
        self,
        name: str,
        url: str,
        phone_number: str,
        create_retailer_presenter: ICreateRetailerPresenter[CreateRetailerViewModel],
    ) -> CreateRetailerViewModel | ErrorViewModel:
        request = CreateRetailerRequest(retailer_uuid=uuid4(), name=name, url=url, phone_number=phone_number)
        result: Result[CreateRetailerResponse] = await self.create_retailer_use_case.execute(request)
        if result.is_succeed:
            success_response: CreateRetailerResponse = result.get_success_value()
            return create_retailer_presenter.present_view_model(success_response)

        error_response: Error = result.get_error_value()
        return create_retailer_presenter.present_error_view_model(error_response)
