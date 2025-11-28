from backend.core.application.patterns.result_type import Result
from backend.core.application.ports.repositories.retailer import IRetailerRepository
from backend.core.application.use_cases.retailer.dtos import CreateRetailerRequest, CreateRetailerResponse
from backend.core.domain.entities.retailer_entity.retailer import Retailer


class CreateRetailerUseCase:
    def __init__(self, retailer_repository: IRetailerRepository) -> None:
        self.retailer_repository = retailer_repository

    async def execute(self, request: CreateRetailerRequest) -> Result[CreateRetailerResponse]:
        retailer = Retailer(
            retailer_uuid=request.retailer_uuid,
            name=request.name,
            url=request.url,
            phone_number=request.phone_number,
        )
        await self.retailer_repository.save(retailer)
        response = CreateRetailerResponse(
            request.retailer_uuid,
            request.name,
        )
        return Result.from_success(response)
