from __future__ import annotations

from dataclasses import dataclass
from typing import override

from metax.core.domain.ddd_patterns import ValueObject
from metax.core.domain.entities.category.errors import (
    CategoryHelperWordsNotFoundForDeletionError,
    DuplicateCategoryHelperWordsError,
)


@dataclass(frozen=True, unsafe_hash=False, eq=True, slots=True)
class CategoryHelperWords(ValueObject):
    words: frozenset[str]

    @override
    @classmethod
    def create(cls, words: frozenset[str]) -> CategoryHelperWords:
        return cls(words=frozenset(words))

    def plus_words(self, new_words: frozenset[str]) -> CategoryHelperWords:
        duplicate_words = self.words & new_words
        if duplicate_words:
            raise DuplicateCategoryHelperWordsError(duplicate_words)
        return type(self).create(words=self.words | new_words)

    def minus_words(self, words_to_delete: frozenset[str]) -> CategoryHelperWords:
        words_to_be_deleted = self.words & words_to_delete
        if not words_to_be_deleted:
            raise CategoryHelperWordsNotFoundForDeletionError(requested_words=words_to_delete)
        return type(self).create(words=self.words - words_to_be_deleted)
