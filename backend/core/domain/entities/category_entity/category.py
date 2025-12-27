from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TypedDict
from uuid import UUID

from backend.core.domain.ddd_patterns import AggregateRootEntity, ValueObject
from backend.core.domain.entities.category_entity.errors.errors import (
    CategoryHelperWordsNotFoundForDeletionError,
    DuplicateCategoryHelperWordsError,
)
from backend.core.domain.entities.category_entity.events import CategoryUpdated


class Category(AggregateRootEntity):
    def __init__(
        self,
        category_uuid: UUID,
        name: str,
        helper_words: CategoryHelperWords,
    ) -> None:
        super().__init__(_uuid=category_uuid)
        self.__name = name
        self.__helper_words = helper_words

    def add_new_helper_words(self, new_words: frozenset[str]) -> None:
        existing_words = self.__helper_words.words
        duplicate_words = existing_words & new_words
        if duplicate_words:
            raise DuplicateCategoryHelperWordsError(duplicate_words)

        updated_words = existing_words | new_words
        self.__helper_words = CategoryHelperWords(words=updated_words)

    def delete_helper_words(self, words_to_delete: frozenset[str]) -> None:
        existing_words = self.__helper_words.words
        words_to_be_deleted = existing_words & words_to_delete
        if not words_to_be_deleted:
            raise CategoryHelperWordsNotFoundForDeletionError(requested_words=words_to_delete)

        updated_words = existing_words - words_to_be_deleted
        self.__helper_words = CategoryHelperWords(words=updated_words)

    def set_name(self, new_name: str) -> None:
        self.__name = new_name

    def get_name(self) -> str:
        return self.__name

    def get_helper_words(self) -> frozenset[str]:
        return self.__helper_words.words

    def update(self, new_data: DataForCategoryUpdate) -> None:
        dispatch_map: dict[str, Callable[[str], None]] = {
            "new_name": self.set_name,
        }
        for key, value in new_data.items():
            handler: Callable[[str], None] | None = dispatch_map.get(key)
            if handler is not None and value is not None and isinstance(value, str):
                handler(value)

        self._record_event(event=CategoryUpdated(category_uuid=self.get_uuid()))


@dataclass(frozen=True, unsafe_hash=False, eq=True, slots=True)
class CategoryHelperWords(ValueObject):
    words: frozenset[str]


class DataForCategoryUpdate(TypedDict):
    new_name: str | None
