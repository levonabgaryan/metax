import logging
from typing import override

from metax.core.application.cud_services.base_cud_service import CUDService
from metax.core.application.cud_services.category.dtos import DeleteCategoryRequestDTO, DeleteCategoryResponseDTO
from metax.core.application.event_handlers.category.events import CategoryDeleted

logger = logging.getLogger(__name__)


class DeleteCategoryService(CUDService[DeleteCategoryRequestDTO]):
    @override
    async def execute(self, request: DeleteCategoryRequestDTO) -> DeleteCategoryResponseDTO:
        logger.info(
            "[RequestDTO: %s] | Status: STARTED | Target UUID: [%s]",
            request.__class__.__name__,
            request.category_uuid,
        )
        uow = await self._unit_of_work_provider.provide()
        async with uow:
            await uow.category_repo.delete_by_uuid(request.category_uuid)
            await uow.commit()
        logger.info(
            "[RequestDTO: %s] | Status: SUCCESS | Target UUID: [%s]",
            request.__class__.__name__,
            request.category_uuid,
        )
        await self._event_bus.emit(CategoryDeleted(category_uuid=request.category_uuid))
        return DeleteCategoryResponseDTO(category_uuid=request.category_uuid)
