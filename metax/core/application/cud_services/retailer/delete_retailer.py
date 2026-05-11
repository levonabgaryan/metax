import logging
from typing import override

from metax.core.application.cud_services.base_cud_service import CUDService
from metax.core.application.cud_services.retailer.dtos import DeleteRetailerRequestDTO, DeleteRetailerResponseDTO
from metax.core.application.event_handlers.retailer.events import RetailerDeleted

logger = logging.getLogger(__name__)


class DeleteRetailerService(CUDService[DeleteRetailerRequestDTO]):
    @override
    async def execute(self, request: DeleteRetailerRequestDTO) -> DeleteRetailerResponseDTO:
        logger.info(
            "[RequestDTO: %s] | Status: STARTED | Target UUID: [%s]",
            request.__class__.__name__,
            request.retailer_uuid,
        )
        uow = await self._unit_of_work_provider.provide()
        async with uow:
            await uow.retailer_repo.delete_by_uuid(request.retailer_uuid)
            await uow.commit()
        logger.info(
            "[RequestDTO: %s] | Status: SUCCESS | Target UUID: [%s]",
            request.__class__.__name__,
            request.retailer_uuid,
        )
        await self._event_bus.emit(RetailerDeleted(retailer_uuid=request.retailer_uuid))
        return DeleteRetailerResponseDTO(retailer_uuid=request.retailer_uuid)
