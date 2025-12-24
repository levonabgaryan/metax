from dataclasses import dataclass
from uuid import UUID

from backend.core.application.patterns.use_case_abc import RequestDTO


@dataclass(frozen=True)
class AddHelperWordsRequest(RequestDTO):
    category_uuid: UUID
    new_helper_words: frozenset[str]


@dataclass(frozen=True)
class DeleteHelperWordsRequest(RequestDTO):
    category_uuid: UUID
    words_to_delete: frozenset[str]
