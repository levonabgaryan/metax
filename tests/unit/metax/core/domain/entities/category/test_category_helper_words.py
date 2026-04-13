import pytest
from core.domain.entities.category.errors import (
    CategoryHelperWordsNotFoundForDeletionError,
    DuplicateCategoryHelperWordsError,
)

from metax.core.domain.entities.category.value_objects import CategoryHelperWords


def test_plus_words_adds_only_new() -> None:
    words = CategoryHelperWords(words=frozenset(("a", "b")))
    result = words.plus_words(frozenset(("c",)))
    assert result.words == frozenset(("a", "b", "c"))


def test_plus_words_rejects_duplicates() -> None:
    words = CategoryHelperWords(words=frozenset(("a", "b", "c")))
    new_words = frozenset(("a", "c"))
    expected_words = ", ".join(sorted(new_words))
    with pytest.raises(DuplicateCategoryHelperWordsError) as err:
        words.plus_words(new_words)
    assert err.value.error_code == "DUPLICATE_HELPER_WORDS"
    assert err.value.title == f"Cannot add duplicate helper words: {expected_words}."


def test_minus_words_removes_intersection() -> None:
    words = CategoryHelperWords(words=frozenset(("a", "b", "c")))
    result = words.minus_words(frozenset(("a", "c")))
    assert result.words == frozenset(("b",))


def test_minus_words_raises_when_nothing_removed() -> None:
    words = CategoryHelperWords(words=frozenset(("a", "b", "c")))
    words_to_delete = frozenset(("d", "e"))
    expected_words = ", ".join(sorted(words_to_delete))
    with pytest.raises(CategoryHelperWordsNotFoundForDeletionError) as err:
        words.minus_words(words_to_delete)
    assert err.value.error_code == "WORDS_NOT_FOUND_FOR_DELETION"
    assert (
        err.value.title
        == f"None of the requested words for deletion ({expected_words}) were found in the existing list."
    )
