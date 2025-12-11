from uuid import uuid4

import pytest

from backend.core.domain.entities.category_entity.category import Category, CategoryHelperWords
from backend.core.domain.entities.category_entity.errors.errors import (
    DuplicateCategoryHelperWordsError,
    CategoryHelperWordsNotFoundForDeletionError,
)


def test_add_new_helper_words() -> None:
    # given
    helper_words = CategoryHelperWords(words=frozenset(("a", "b", "c")))
    category = Category(category_uuid=uuid4(), name="test_name", helper_words=helper_words)
    new_words = frozenset(("a", "c"))

    # when
    with pytest.raises(DuplicateCategoryHelperWordsError) as err:
        category.add_new_helper_words(new_words=new_words)

    # except
    assert err.value.error_code == "DUPLICATE_HELPER_WORDS"
    assert err.value.message == f"Cannot add duplicate helper words: {', '.join(new_words)}."


def test_delete_helper_words() -> None:
    # given
    helper_words = CategoryHelperWords(words=frozenset(("a", "b", "c")))
    category = Category(category_uuid=uuid4(), name="test_name", helper_words=helper_words)
    words_to_delete = frozenset(("d", "e"))

    # when
    with pytest.raises(CategoryHelperWordsNotFoundForDeletionError) as err:
        category.delete_helper_words(words_to_delete)

    # then
    assert err.value.error_code == "WORDS_NOT_FOUND_FOR_DELETION"
    assert (
        err.value.message
        == f"None of the requested words for deletion ({', '.join(words_to_delete)}) were found in the existing list."
    )
