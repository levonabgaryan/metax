import logging
from typing import override

from metax.core.application.cud_services.base_cud_service import CUDService
from metax.core.application.cud_services.category.dtos import (
    UpdateCategoryRequestDTO,
    UpdateCategoryResponseDTO,
)

logger = logging.getLogger(__name__)


class UpdateCategoryService(CUDService[UpdateCategoryRequestDTO]):
    @override
    async def execute(self, request: UpdateCategoryRequestDTO) -> UpdateCategoryResponseDTO:
        logger.info(
            "[RequestDTO: %s] | Status: STARTED | Target UUID: [%s]",
            request.__class__.__name__,
            request.category_uuid,
        )
        uow = await self._unit_of_work_provider.provide()
        async with uow:
            repo = uow.category_repo
            category = await repo.get_by_uuid(request.category_uuid)
            if request.new_name is not None:
                category.set_name(request.new_name)
            if request.new_name_hy is not None:
                category.set_name_hy(request.new_name_hy)
            if request.new_name_ru is not None:
                category.set_name_ru(request.new_name_ru)
            await repo.update(updated_category=category)
            await uow.commit()
        logger.info(
            "[RequestDTO: %s] | Status: SUCCESS | Target UUID: [%s]",
            request.__class__.__name__,
            category.get_uuid(),
        )
        return UpdateCategoryResponseDTO(
            category_uuid=category.get_uuid(),
            created_at=category.get_created_at(),
            updated_at=category.get_updated_at(),
            name=category.get_name(),
            name_hy=category.get_name_hy(),
            name_ru=category.get_name_ru(),
        )
