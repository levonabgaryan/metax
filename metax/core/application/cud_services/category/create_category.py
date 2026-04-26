import logging
import uuid
from datetime import UTC, datetime
from typing import override

from metax.core.application.cud_services.base_cud_service import CUDService
from metax.core.application.cud_services.category.dtos import (
    CreateCategoryRequestDTO,
    CreateCategoryResponseDTO,
    HelperWordPayload,
)
from metax.core.domain.entities.category.aggregate_root_entity import Category
from metax.core.domain.entities.category_helper_word.entity import CategoryHelperWord

logger = logging.getLogger(__name__)


class CreateCategoryService(CUDService[CreateCategoryRequestDTO]):
    @override
    async def execute(self, request: CreateCategoryRequestDTO) -> CreateCategoryResponseDTO:
        uow = await self._unit_of_work_provider.provide()
        async with uow:
            logger.info(
                "[RequestDTO: %s] | Status: STARTED | Target UUID: [%s]",
                request.__class__.__name__,
                request.category_uuid,
            )
            now = datetime.now(tz=UTC)
            helper_words = [
                CategoryHelperWord(
                    uuid_=uuid.uuid7(),
                    created_at=now,
                    updated_at=now,
                    text=helper_word_payload.text,
                )
                for helper_word_payload in request.helper_words_payload
            ]
            category = Category(
                uuid_=request.category_uuid,
                name=request.name,
                helper_words=helper_words,
                created_at=now,
                updated_at=now,
            )
            repo = uow.category_repo
            await repo.add(category)
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
