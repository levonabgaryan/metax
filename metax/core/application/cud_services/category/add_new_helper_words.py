import logging
import uuid
from datetime import UTC, datetime
from typing import override

from metax.core.application.cud_services.base_cud_service import CUDService
from metax.core.application.cud_services.category.dtos import (
    AddNewHelperWordsRequestDTO,
    AddNewHelperWordsResponseDTO,
    HelperWordPayload,
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
                    text=helper_word.text,
                )
                for helper_word in request.new_helper_words_payload
            ]
            category.add_new_helper_words(new_helper_words_entities)
            await repo.update(updated_category=category)
            await uow.commit()
        logger.info(
            "[RequestDTO: %s] | Status: SUCCESS | Target UUID: [%s]",
            request.__class__.__name__,
            category.get_uuid(),
        )
        return AddNewHelperWordsResponseDTO(
            category_uuid=category.get_uuid(),
            new_helper_words_payload=[
                HelperWordPayload(
                    text=helper_word.get_text(),
                    helper_word_uuid=helper_word.get_uuid(),
                    created_at=helper_word.get_created_at(),
                    updated_at=helper_word.get_updated_at(),
                )
                for helper_word in category.get_helper_words()
            ],
            created_at=category.get_created_at(),
            updated_at=category.get_updated_at(),
            name=category.get_name(),
        )
