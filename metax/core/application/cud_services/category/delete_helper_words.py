import logging
from typing import override

from metax.core.application.cud_services.base_cud_service import CUDService
from metax.core.application.cud_services.category.dtos import (
    DeleteHelperWordRequestDTO,
    DeleteHelperWordResponseDTO,
    HelperWordPayloadResponseDTO,
)

logger = logging.getLogger(__name__)


class DeleteHelperWordService(CUDService[DeleteHelperWordRequestDTO]):
    @override
    async def execute(self, request: DeleteHelperWordRequestDTO) -> DeleteHelperWordResponseDTO:
        logger.info(
            "[RequestDTO: %s] | Status: STARTED | Target UUID: [%s]",
            request.__class__.__name__,
            request.category_uuid,
        )
        uow = await self._unit_of_work_provider.provide()
        async with uow:
            repo = uow.category_repo
            category = await repo.get_by_uuid(request.category_uuid)
            helper_word_to_delete = next(
                helper_word
                for helper_word in category.get_helper_words()
                if helper_word.get_uuid() == request.helper_word_uuid
            )
            category.delete_helper_words_by_uuids(uuids=[request.helper_word_uuid])
            await repo.update(updated_category=category)
            await uow.commit()
        logger.info(
            "[RequestDTO: %s] | Status: SUCCESS | Target UUID: [%s]",
            request.__class__.__name__,
            category.get_uuid(),
        )
        return DeleteHelperWordResponseDTO(
            category_uuid=category.get_uuid(),
            created_at=category.get_created_at(),
            updated_at=category.get_updated_at(),
            name=category.get_name(),
            deleted_helper_word_payload=HelperWordPayloadResponseDTO(
                helper_word_text=helper_word_to_delete.get_helper_word_text(),
                helper_word_uuid=helper_word_to_delete.get_uuid(),
                created_at=helper_word_to_delete.get_created_at(),
                updated_at=helper_word_to_delete.get_updated_at(),
            ),
        )
