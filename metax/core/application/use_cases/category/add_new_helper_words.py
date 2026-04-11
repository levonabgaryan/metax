import logging
from dataclasses import dataclass
from typing import override
from uuid import UUID

from metax.core.application.use_cases.base_use_case import RequestDTO, ResponseDTO, UseCase

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AddNewHelperWordsRequest(RequestDTO):
    category_uuid: UUID
    new_helper_words: frozenset[str]


class AddNewHelperWords(UseCase[AddNewHelperWordsRequest]):
    @override
    async def handle_use_case(self, request: AddNewHelperWordsRequest) -> ResponseDTO:
        logger.info(
            "[Use case: %s] | Status: STARTED | Target UUID: [%s]",
            self.__class__.__name__,
            request.category_uuid,
        )
        uow = await self._unit_of_work_provider.create()
        async with uow:
            repo = uow.category_repo
            category = await repo.get_by_uuid(request.category_uuid)
            category.add_new_helper_words(request.new_helper_words)
            await repo.add_new_helper_words_by_category_uuid(
                category_uuid=request.category_uuid,
                new_helper_words=request.new_helper_words,
            )
            await uow.commit()
        logger.info(
            "[Use case: %s] | Status: SUCCESS | Target UUID: [%s]",
            self.__class__.__name__,
            category.get_uuid(),
        )
        return ResponseDTO()
