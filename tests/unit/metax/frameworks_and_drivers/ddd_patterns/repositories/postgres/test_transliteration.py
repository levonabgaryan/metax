"""Unit tests for Armenian -> Latin phonetic transliteration used by cross-script search."""

from __future__ import annotations

import pytest

from metax.frameworks_and_drivers.ddd_patterns.repositories.postgres.transliteration import (
    transliterate_armenian_to_latin,
)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("կարագ", "karag"),  # the motivating case: butter
        ("Կարագ", "karag"),  # uppercase folds to the same key
        ("կաթ", "kat"),  # plain word
        ("պանիր", "panir"),  # cheese
        ("ձու", "dzu"),  # "ու" digraph -> u, "ձ" -> dz
        ("շոկոլադ", "shokolad"),  # multi-letter digraphs (sh)
        ("և", "ev"),  # ligature
    ],
)
def test_transliterates_armenian_words(source: str, expected: str) -> None:
    assert transliterate_armenian_to_latin(source) == expected


def test_latin_and_other_characters_pass_through_lowercased() -> None:
    # Already-Latin brand names and any non-Armenian characters are kept (just lower-cased), so the
    # function is a safe no-op normaliser for Latin queries.
    assert transliterate_armenian_to_latin("Coca Cola 1.5L") == "coca cola 1.5l"


def test_mixed_script_is_transliterated_per_character() -> None:
    assert transliterate_armenian_to_latin("կարագ Premium") == "karag premium"
