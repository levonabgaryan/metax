from dataclasses import dataclass
from uuid import UUID

@dataclass(frozen=True)
class CreateCategoryRequest:
    category_uuid: UUID
    name: str
    helper_words: frozenset[str]

@dataclass(frozen=True)
class CreateCategoryResponse:
    category_uuid: UUID
    name: str
