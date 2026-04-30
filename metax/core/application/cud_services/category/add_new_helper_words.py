import logging
import uuid
from datetime import UTC, datetime
from typing import override

from metax.core.application.cud_services.base_cud_service import CUDService
from metax.core.application.cud_services.category.dtos import (
    AddNewHelperWordsRequestDTO,
    AddNewHelperWordsResponseDTO,
    HelperWordPayloadResponseDTO,
)
from metax.core.domain.entities.category_helper_word.entity import CategoryHelperWord

logger = logging.getLogger(__name__)


class AddNewHelperWordsService(CUDService[AddNewHelperWordsRequestDTO]):
    @override
    async def execute(self, request: AddNewHelperWordsRequestDTO) -> AddNewHelperWordsResponseDTO:
        logger.info(
            "[RequestDTO: %s] | Status: STARTED | Target UUID: [%s]",
            request.__class__.__name__,
            request.category_uuid,
        )
        now = datetime.now(tz=UTC)

        uow = await self._unit_of_work_provider.provide()
        async with uow:
            repo = uow.category_repo
            category = await repo.get_by_uuid(request.category_uuid)
            new_helper_words_entities = [
                CategoryHelperWord(
                    uuid_=uuid.uuid7(),
                    created_at=now,
                    updated_at=now,
                    helper_word_text=request.new_helper_word_payload.helper_word_text,
                )
            ]
            category.add_new_helper_words(new_helper_words_entities)
            await repo.update(updated_category=category)
            await uow.commit()
        logger.info(
            "[RequestDTO: %s] | Status: SUCCESS | Target UUID: [%s]",
            request.__class__.__name__,
            category.get_uuid(),
        )
        added_helper_word = new_helper_words_entities[0]
        return AddNewHelperWordsResponseDTO(
            category_uuid=category.get_uuid(),
            new_helper_word_payload=HelperWordPayloadResponseDTO(
                helper_word_text=added_helper_word.get_helper_word_text(),
                helper_word_uuid=added_helper_word.get_uuid(),
                created_at=added_helper_word.get_created_at(),
                updated_at=added_helper_word.get_updated_at(),
            ),
            created_at=category.get_created_at(),
            updated_at=category.get_updated_at(),
            name=category.get_name(),
        )
