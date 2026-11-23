"""Unit tests for the exact-keyword tier of category classification."""

from __future__ import annotations

import importlib

import pytest

from metax.core.application.ddd_patterns.services.category_keyword_matcher import (
    CategoryKeywordMatcher,
    find_keyword_conflicts,
    product_noun_phrase,
)
from metax.core.domain.entities.category.aggregate_root_entity import Category
from tests.utils import make_category_entity


def _category(name: str, keywords: list[str]) -> Category:
    category = make_category_entity(name=name)
    category.set_keywords(keywords)
    return category


def _matched_category_name(
    matcher: CategoryKeywordMatcher, categories: list[Category], product: str
) -> str | None:
    match = matcher.match(product)
    if match is None:
        return None
    return next(category.get_name() for category in categories if category.get_uuid() == match.category_uuid)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Շամպուն «Dove Ultra Care» 400մլ", "Շամպուն"),
        ("Պանիր հալած «Հոխլանդ» խոզապուխտով 140գր", "Պանիր հալած"),
        ("«Coca-Cola» 1.5լ", "«Coca-Cola» 1.5լ"),  # starts with the brand: keep the whole name
        ("Սառույցի կաղապար 1 հատ", "Սառույցի կաղապար 1 հատ"),
    ],
)
def test_product_noun_phrase_drops_the_brand_and_what_follows(name: str, expected: str) -> None:
    assert product_noun_phrase(name) == expected


def test_short_keywords_match_whole_words_only() -> None:
    # "ձու" (egg) must not match "ձուկ" (fish)
    categories = [_category("Eggs", ["ձու"]), _category("Fish", ["ձուկ"])]
    matcher = CategoryKeywordMatcher(categories)

    assert _matched_category_name(matcher, categories, "Ձուկ սառեցված") == "Fish"
    assert _matched_category_name(matcher, categories, "Ձու հավի 10 հատ") == "Eggs"


def test_long_keywords_also_match_inflected_forms() -> None:
    categories = [_category("Food", ["շոկոլադ", "կոնֆետ"])]
    matcher = CategoryKeywordMatcher(categories)

    assert _matched_category_name(matcher, categories, "Շոկոլադե սալիկ «Milka»") == "Food"
    assert _matched_category_name(matcher, categories, "Կոնֆետների հավաքածու «Բաչի»") == "Food"


def test_longer_phrase_overrides_a_single_word() -> None:
    categories = [_category("Drinks", ["ջուր"]), _category("Beauty", ["միցելային ջուր"])]
    matcher = CategoryKeywordMatcher(categories)

    assert _matched_category_name(matcher, categories, "Միցելային ջուր «Նիվեա» 400մլ") == "Beauty"
    assert _matched_category_name(matcher, categories, "Ջուր «Բջնի» 1լ") == "Drinks"


def test_earliest_word_wins_between_single_words() -> None:
    # The head noun comes first: a sauce dish is tableware, not sauce.
    categories = [_category("Food", ["սոուս"]), _category("Household", ["ափսե"])]
    matcher = CategoryKeywordMatcher(categories)

    assert _matched_category_name(matcher, categories, "Ափսե սոուսի համար") == "Household"


def test_longer_keyword_wins_over_its_own_stem() -> None:
    categories = [_category("Food", ["շաքար"]), _category("Household", ["շաքարաման"])]
    matcher = CategoryKeywordMatcher(categories)

    assert _matched_category_name(matcher, categories, "Շաքարաման ապակե") == "Household"


def test_keywords_in_the_brand_are_ignored() -> None:
    categories = [_category("Food", ["կաթ"])]
    matcher = CategoryKeywordMatcher(categories)

    assert matcher.match("Ափսե «Կաթ» 20սմ") is None


def test_a_keyword_listed_under_two_categories_is_ignored() -> None:
    categories = [_category("Hardware", ["ներկ"]), _category("Stationery", ["ներկ"])]

    assert CategoryKeywordMatcher(categories).match("Ներկ սպիտակ") is None
    assert find_keyword_conflicts({"Hardware": ["ներկ"], "Stationery": ["Ներկ"]}) == {
        ("ներկ",): {"Hardware", "Stationery"}
    }


def test_seeded_keyword_lists_have_no_conflicts() -> None:
    seed = importlib.import_module(
        "metax.frameworks_and_drivers.django_framework.django_framework.metax.migrations.0003_categorymodel_keywords"
    )

    assert find_keyword_conflicts(seed._KEYWORDS) == {}  # noqa: SLF001
