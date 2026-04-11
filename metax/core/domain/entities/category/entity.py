from __future__ import annotations

from typing import Callable, TypedDict
from uuid import UUID

from metax.core.domain.ddd_patterns import AggregateRootEntity

from .value_objects import CategoryHelperWords


class Category(AggregateRootEntity):
    def __init__(
        self,
        category_uuid: UUID,
        name: str,
        helper_words: CategoryHelperWords,
    ) -> None:
        super().__init__(uuid_=category_uuid)
        self.__name = name
        self.__helper_words = helper_words

    def add_new_helper_words(self, new_words: frozenset[str]) -> None:
        self.__helper_words = self.__helper_words.plus_words(new_words)

    def delete_helper_words(self, words_to_delete: frozenset[str]) -> None:
        self.__helper_words = self.__helper_words.minus_words(words_to_delete)

    def set_name(self, new_name: str) -> None:
        self.__name = new_name

    def get_name(self) -> str:
        return self.__name

    def get_helper_words(self) -> frozenset[str]:
        return self.__helper_words.words

    def set_helper_words(self, helper_words: CategoryHelperWords) -> None:
        self.__helper_words = helper_words

    def update(self, new_data: DataForCategoryUpdate) -> None:
        dispatch_map: dict[str, Callable[[str], None]] = {
            "new_name": self.set_name,
        }
        for key, value in new_data.items():
            handler: Callable[[str], None] | None = dispatch_map.get(key)
            if handler is not None and value is not None and isinstance(value, str):
                handler(value)


class DataForCategoryUpdate(TypedDict):
    new_name: str | None
