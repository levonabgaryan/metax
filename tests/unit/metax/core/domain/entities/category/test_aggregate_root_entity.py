from datetime import UTC, datetime
from uuid import uuid7

import pytest

from metax.core.domain.entities.category.aggregate_root_entity import Category
from metax.core.domain.entities.category.errors import (
    DuplicateCategoryHelperWordsError,
)
from metax.core.domain.entities.category_helper_word.entity import CategoryHelperWord


def _make_helper_word(text: str) -> CategoryHelperWord:
    ts = datetime(2026, 1, 1, tzinfo=UTC)
    return CategoryHelperWord(
        uuid_=uuid7(),
        helper_word_text=text,
        created_at=ts,
        updated_at=ts,
    )


def test_add_new_helper_words() -> None:
    # given
    ts = datetime(2026, 1, 1, tzinfo=UTC)
    category = Category(
        uuid_=uuid7(),
        name="test_name",
        helper_words=[_make_helper_word("a"), _make_helper_word("b"), _make_helper_word("c")],
        created_at=ts,
        updated_at=ts,
    )
    new_words = [_make_helper_word("a"), _make_helper_word("c")]

    # when
    with pytest.raises(DuplicateCategoryHelperWordsError) as err:
        category.add_new_helper_words(new_words)

    # except
    assert err.value.error_code == "DUPLICATE_HELPER_WORDS"
    assert err.value.title == "Cannot add duplicate helper words: a, c."


def test_delete_helper_words_by_uuids() -> None:
    # given
    ts = datetime(2026, 1, 1, tzinfo=UTC)
    word_a = _make_helper_word("a")
    word_b = _make_helper_word("b")
    word_c = _make_helper_word("c")
    category = Category(
        uuid_=uuid7(),
        name="test_name",
        helper_words=[word_a, word_b, word_c],
        created_at=ts,
        updated_at=ts,
    )
    words_to_delete = [word_a.get_uuid(), word_c.get_uuid()]

    category.delete_helper_words_by_uuids(words_to_delete)
    assert [word.get_helper_word_text() for word in category.get_helper_words()] == ["b"]
