import logging
from typing import override

from metax.core.application.cud_services.base_cud_service import CUDService
from metax.core.application.cud_services.category.dtos import (
    HelperWordPayload,
    UpdateHelperWordTextRequestDTO,
    UpdateHelperWordTextResponseDTO,
)

logger = logging.getLogger(__name__)


class UpdateHelperWordTextService(CUDService[UpdateHelperWordTextRequestDTO]):
    @override
    async def execute(self, request: UpdateHelperWordTextRequestDTO) -> UpdateHelperWordTextResponseDTO:
        logger.info(
            "[RequestDTO: %s] | Status: STARTED | Target UUID: [%s]",
            request.__class__.__name__,
            request.category_uuid,
        )
        uow = await self._unit_of_work_provider.provide()
        async with uow:
            repo = uow.category_repo
            category = await repo.get_by_uuid(request.category_uuid)
            category.update_helper_word_text_by_uuid(
                helper_word_uuid=request.helper_word_uuid,
                text=request.new_text,
            )
            await repo.update(updated_category=category)
            await uow.commit()
        logger.info(
            "[RequestDTO: %s] | Status: SUCCESS | Target UUID: [%s]",
            request.__class__.__name__,
            category.get_uuid(),
        )
        return UpdateHelperWordTextResponseDTO(
            category_uuid=category.get_uuid(),
            created_at=category.get_created_at(),
            updated_at=category.get_updated_at(),
            name=category.get_name(),
            helper_words_payload=[
                HelperWordPayload(
                    text=helper_word.get_text(),
                    helper_word_uuid=helper_word.get_uuid(),
                    created_at=helper_word.get_created_at(),
                    updated_at=helper_word.get_updated_at(),
                )
                for helper_word in category.get_helper_words()
            ],
        )
