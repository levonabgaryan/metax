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


@dataclass(frozen=True)
class AddNewCategoryHelperWordsRequest:
    category_name: str
    new_helper_words: frozenset[str]


@dataclass(frozen=True)
class DeleteCategoryHelperWordsRequest:
    category_name: str
    words_to_delete: frozenset[str]
