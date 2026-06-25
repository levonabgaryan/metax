import datetime as dt
from uuid import uuid7

from metax.core.domain.entities.category.aggregate_root_entity import Category

_TS = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)


def _make_category() -> Category:
    return Category(
        uuid_=uuid7(),
        name="dairy",
        name_hy="կաթ",
        name_ru="молоко",
        created_at=_TS,
        updated_at=_TS,
    )


def test_category_exposes_multilingual_names() -> None:
    category = _make_category()

    assert category.get_name() == "dairy"
    assert category.get_name_hy() == "կաթ"
    assert category.get_name_ru() == "молоко"


def test_category_defaults_translations_to_empty_strings() -> None:
    category = Category(uuid_=uuid7(), name="meat", created_at=_TS, updated_at=_TS)

    assert category.get_name_hy() == ""
    assert category.get_name_ru() == ""


def test_set_name_updates_value_and_touches_updated_at() -> None:
    category = _make_category()

    category.set_name("dairy products")

    assert category.get_name() == "dairy products"
    assert category.get_updated_at() > _TS


def test_set_translations_update_values() -> None:
    category = _make_category()

    category.set_name_hy("կաթնամթերք")
    category.set_name_ru("молочные продукты")

    assert category.get_name_hy() == "կաթնամթերք"
    assert category.get_name_ru() == "молочные продукты"
