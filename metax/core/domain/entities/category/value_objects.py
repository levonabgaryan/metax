from __future__ import annotations

from dataclasses import dataclass

from metax.core.domain.ddd_patterns import ValueObject

from .errors.errors import (
    CategoryHelperWordsNotFoundForDeletionError,
    DuplicateCategoryHelperWordsError,
)


@dataclass(frozen=True, unsafe_hash=False, eq=True, slots=True)
class CategoryHelperWords(ValueObject):
    words: frozenset[str]

    def plus_words(self, new_words: frozenset[str]) -> CategoryHelperWords:
        duplicate_words = self.words & new_words
        if duplicate_words:
            raise DuplicateCategoryHelperWordsError(duplicate_words)
        return CategoryHelperWords(words=self.words | new_words)

    def minus_words(self, words_to_delete: frozenset[str]) -> CategoryHelperWords:
        words_to_be_deleted = self.words & words_to_delete
        if not words_to_be_deleted:
            raise CategoryHelperWordsNotFoundForDeletionError(requested_words=words_to_delete)
        return CategoryHelperWords(words=self.words - words_to_be_deleted)
