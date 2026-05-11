import logging
from typing import override

from metax.core.application.cud_services.base_cud_service import CUDService
from metax.core.application.cud_services.category.dtos import (
    HelperWordPayloadRequestDTO,
    UpdateCategoryRequestDTO,
    UpdateCategoryResponseDTO,
)
from metax.core.application.event_handlers.category.events import CategoryUpdated

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

            await repo.update(updated_category=category)
            await uow.commit()
        logger.info(
            "[RequestDTO: %s] | Status: SUCCESS | Target UUID: [%s]",
            request.__class__.__name__,
            category.get_uuid(),
        )
        event = CategoryUpdated(category_uuid=category.get_uuid())
        await self._event_bus.emit(event)
        return UpdateCategoryResponseDTO(
            category_uuid=category.get_uuid(),
            created_at=category.get_created_at(),
            updated_at=category.get_updated_at(),
            name=category.get_name(),
            helper_words_payload=[
                HelperWordPayloadRequestDTO(
                    helper_word_text=helper_word.get_helper_word_text(),
                    helper_word_uuid=helper_word.get_uuid(),
                    created_at=helper_word.get_created_at(),
                    updated_at=helper_word.get_updated_at(),
                )
                for helper_word in category.get_helper_words()
            ],
        )
