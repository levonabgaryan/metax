import logging
from datetime import UTC, datetime
from typing import override

from metax.core.application.cud_services.base_cud_service import CUDService
from metax.core.application.cud_services.retailer.dtos import CreateRetailerRequestDTO, CreateRetailerResponseDTO
from metax.core.domain.entities.retailer.aggregate_root_entity import Retailer

logger = logging.getLogger(__name__)


class CreateRetailerService(CUDService[CreateRetailerRequestDTO]):
    @override
    async def execute(self, request: CreateRetailerRequestDTO) -> CreateRetailerResponseDTO:
        logger.info(
            "[RequestDTO: %s] | Status: STARTED | Target UUID: [%s]",
            request.__class__.__name__,
            request.retailer_uuid,
        )
        uow = await self._unit_of_work_provider.provide()
        async with uow:
            now = datetime.now(tz=UTC)
            retailer = Retailer(
                uuid_=request.retailer_uuid,
                name=request.name,
                phone_number=request.phone_number,
                home_page_url=request.url,
                created_at=now,
                updated_at=now,
            )
            await uow.retailer_repo.add(retailer)
            await uow.commit()
        logger.info(
            "[RequestDTO: %s] | Status: SUCCESS | Target UUID: [%s]",
            request.__class__.__name__,
            retailer.get_uuid(),
        )
        return CreateRetailerResponseDTO(
            retailer_uuid=retailer.get_uuid(),
            name=retailer.get_name(),
            phone_number=retailer.get_phone_number(),
            home_page_url=retailer.get_home_page_url(),
            created_at=retailer.get_created_at(),
            updated_at=retailer.get_updated_at(),
        )
