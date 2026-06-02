import datetime as dt
import logging
import uuid
from typing import override

from metax.core.application.cud_services.base_cud_service import CUDService
from metax.core.application.cud_services.category.dtos import (
    CreateCategoryRequestDTO,
    CreateCategoryResponseDTO,
)
from metax.core.domain.entities.category.aggregate_root_entity import Category

logger = logging.getLogger(__name__)


class CreateCategoryService(CUDService[CreateCategoryRequestDTO]):
    @override
    async def execute(self, request: CreateCategoryRequestDTO) -> CreateCategoryResponseDTO:
        uow = await self._unit_of_work_provider.provide()
        async with uow:
            category_uuid = uuid.uuid7()
            logger.info(
                "[RequestDTO: %s] | Status: STARTED | Target UUID: [%s]",
                request.__class__.__name__,
                category_uuid,
            )
            now = dt.datetime.now(tz=dt.UTC)
            category = Category(
                uuid_=category_uuid,
                name=request.name,
                name_hy=request.name_hy,
                name_ru=request.name_ru,
                created_at=now,
                updated_at=now,
            )
            await uow.category_repo.add(category)
            await uow.commit()
        logger.info(
            "[RequestDTO: %s] | Status: SUCCESS | Target UUID: [%s]",
            request.__class__.__name__,
            category.get_uuid(),
        )
        return CreateCategoryResponseDTO(
            category_uuid=category.get_uuid(),
            created_at=category.get_created_at(),
            updated_at=category.get_updated_at(),
            name=category.get_name(),
            name_hy=category.get_name_hy(),
            name_ru=category.get_name_ru(),
        )
