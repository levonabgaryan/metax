from uuid import uuid4

import pytest

from metax.core.domain.entities.category.entity import Category
from metax.core.domain.entities.category.errors.errors import (
    CategoryHelperWordsNotFoundForDeletionError,
    DuplicateCategoryHelperWordsError,
)
from metax.core.domain.entities.category.value_objects import CategoryHelperWords


def test_add_new_helper_words() -> None:
    # given
    helper_words = CategoryHelperWords(words=frozenset(("a", "b", "c")))
    category = Category(category_uuid=uuid4(), name="test_name", helper_words=helper_words)
    new_words = frozenset(("a", "c"))

    expected_words = ", ".join(sorted(new_words))

    # when
    with pytest.raises(DuplicateCategoryHelperWordsError) as err:
        category.add_new_helper_words(new_words=new_words)

    # except
    assert err.value.error_code == "DUPLICATE_HELPER_WORDS"
    assert err.value.title == f"Cannot add duplicate helper words: {expected_words}."


def test_delete_helper_words() -> None:
    # given
    helper_words = CategoryHelperWords(words=frozenset(("a", "b", "c")))
    category = Category(category_uuid=uuid4(), name="test_name", helper_words=helper_words)
    words_to_delete = frozenset(("d", "e"))
    expected_words = ", ".join(sorted(words_to_delete))

    # when
    with pytest.raises(CategoryHelperWordsNotFoundForDeletionError) as err:
        category.delete_helper_words(words_to_delete)

    # then
    assert err.value.error_code == "WORDS_NOT_FOUND_FOR_DELETION"
    assert (
        err.value.title
        == f"None of the requested words for deletion ({expected_words}) were found in the existing list."
    )
