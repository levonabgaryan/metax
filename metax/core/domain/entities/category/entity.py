from __future__ import annotations

from metax.core.domain.ddd_patterns import AggregateRootEntity
from metax.core.domain.general_value_objects import EntityDateTimeDetails, UUIDValueObject

from .value_objects import CategoryHelperWords


class Category(AggregateRootEntity):
    def __init__(
        self,
        category_uuid: UUIDValueObject,
        name: str,
        helper_words: CategoryHelperWords,
        datetime_details: EntityDateTimeDetails,
    ) -> None:
        super().__init__(uuid_value_object=category_uuid, datetime_details=datetime_details)
        self.__name = name
        self.__helper_words = helper_words

    def add_new_helper_words(self, new_words: frozenset[str]) -> None:
        self.__helper_words = self.__helper_words.plus_words(new_words)

    def delete_helper_words(self, words_to_delete: frozenset[str]) -> None:
        self.__helper_words = self.__helper_words.minus_words(words_to_delete)

    def get_name(self) -> str:
        return self.__name

    def set_name(self, new_name: str) -> None:
        self.__name = new_name

    def get_helper_words(self) -> frozenset[str]:
        return self.__helper_words.words

    def set_helper_words(self, helper_words: CategoryHelperWords) -> None:
        self.__helper_words = helper_words
