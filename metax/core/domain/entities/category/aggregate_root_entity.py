from __future__ import annotations

from datetime import datetime
from uuid import UUID

from metax.core.domain.ddd_patterns import AggregateRootEntity
from metax.core.domain.ddd_patterns.general_value_objects import EntityDateTimeDetails, UUIDValueObject
from metax.core.domain.entities.category_helper_word.entity import CategoryHelperWord

from .errors import DuplicateCategoryHelperWordsError


class Category(AggregateRootEntity):
    def __init__(
        self,
        uuid_: UUID,
        created_at: datetime,
        updated_at: datetime,
        helper_words: list[CategoryHelperWord],
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
        self.__helper_words = helper_words

    def add_new_helper_words(self, new_helper_words: list[CategoryHelperWord]) -> None:
        new_helper_words_texts = [helper_word.get_helper_word_text() for helper_word in new_helper_words]
        self.__check_texts_uniqueness(new_helper_words_texts)
        self.__helper_words.extend(new_helper_words)
        self._touch()

    def delete_helper_words_by_uuids(self, uuids: list[UUID]) -> None:
        uuids_to_delete = frozenset(uuids)
        self.__helper_words = [
            helper_word for helper_word in self.__helper_words if helper_word.get_uuid() not in uuids_to_delete
        ]
        self._touch()

    def get_helper_words(self) -> list[CategoryHelperWord]:
        return self.__helper_words

    def get_name(self) -> str:
        return self.__name

    def set_name(self, new_name: str) -> None:
        self.__name = new_name
        self._touch()

    def update_helper_word_text_by_uuid(self, helper_word_uuid: UUID, text: str) -> None:
        self.__check_texts_uniqueness([text])
        for helper_word in self.__helper_words:
            if helper_word.get_uuid() == helper_word_uuid:
                helper_word.set_helper_word_text(text)
                break
        self._touch()

    def __check_texts_uniqueness(self, texts: list[str]) -> None:
        """Checks if texts already has been contained in current helper words.

        Raises:
            DuplicateCategoryHelperWordsError: If any text already exists in category helper words.
        """
        current_helper_words_texts = frozenset(
            helper_word.get_helper_word_text() for helper_word in self.__helper_words
        )
        new_helper_words_texts = frozenset(texts)
        duplicate_texts = current_helper_words_texts.intersection(new_helper_words_texts)

        if duplicate_texts:
            raise DuplicateCategoryHelperWordsError(frozenset(duplicate_texts))
