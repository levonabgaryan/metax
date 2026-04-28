import logging
from typing import override

from metax.core.application.cud_services.base_cud_service import CUDService
from metax.core.application.cud_services.retailer.dtos import UpdateRetailerRequestDTO, UpdateRetailerResponseDTO
from metax.core.application.event_handlers.retailer.events import RetailerUpdated

logger = logging.getLogger(__name__)


class UpdateRetailerService(CUDService[UpdateRetailerRequestDTO]):
    @override
    async def execute(self, request: UpdateRetailerRequestDTO) -> UpdateRetailerResponseDTO:
        logger.info(
            "[RequestDTO: %s] | Status: STARTED | Target UUID: [%s]",
            request.__class__.__name__,
            request.retailer_uuid,
        )
        uow = await self._unit_of_work_provider.provide()
        async with uow:
            repo = uow.retailer_repo
            retailer = await repo.get_by_uuid(request.retailer_uuid)
            if request.new_name is not None:
                retailer.set_name(request.new_name)
            if request.new_url is not None:
                retailer.set_home_page_url(request.new_url)
            if request.new_phone_number is not None:
                retailer.set_phone_number(request.new_phone_number)

            await repo.update(updated_retailer=retailer)
            await uow.commit()
        logger.info(
            "[RequestDTO: %s] | Status: SUCCESS | Target UUID: [%s]",
            request.__class__.__name__,
            retailer.get_uuid(),
        )
        event = RetailerUpdated(retailer_uuid=retailer.get_uuid())
        await self._event_bus.emit(event)
        return UpdateRetailerResponseDTO(
            retailer_uuid=retailer.get_uuid(),
            new_name=retailer.get_name(),
            new_url=retailer.get_home_page_url(),
            new_phone_number=retailer.get_phone_number(),
            created_at=retailer.get_created_at(),
            updated_at=retailer.get_updated_at(),
        )
