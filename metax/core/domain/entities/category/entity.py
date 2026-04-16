from __future__ import annotations

from datetime import datetime
from uuid import UUID

from metax.core.domain.ddd_patterns import AggregateRootEntity
from metax.core.domain.ddd_patterns.general_value_objects import EntityDateTimeDetails, UUIDValueObject

from .value_objects import CategoryHelperWords


class Category(AggregateRootEntity):
    def __init__(
        self,
        uuid_: UUID,
        helper_words: frozenset[str],
        created_at: datetime,
        updated_at: datetime,
        name: str,
    ) -> None:
        super().__init__(
            uuid_value_object=UUIDValueObject.create(uuid_),
            datetime_details=EntityDateTimeDetails.create(
                created_at=created_at,
                updated_at=updated_at,
            ),
        )
        self.__name = name
        self.__helper_words = CategoryHelperWords.create(words=helper_words)

    def add_new_helper_words(self, new_words: frozenset[str]) -> None:
        self.__helper_words = self.__helper_words.plus_words(new_words)
        self._touch()

    def delete_helper_words(self, words_to_delete: frozenset[str]) -> None:
        self.__helper_words = self.__helper_words.minus_words(words_to_delete)
        self._touch()

    def get_name(self) -> str:
        return self.__name

    def set_name(self, new_name: str) -> None:
        self.__name = new_name
        self._touch()

    def get_helper_words(self) -> frozenset[str]:
        return self.__helper_words.words

    def set_helper_words(self, helper_words: frozenset[str]) -> None:
        self.__helper_words = CategoryHelperWords.create(words=helper_words)
        self._touch()
