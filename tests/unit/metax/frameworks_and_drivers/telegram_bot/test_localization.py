"""Unit tests for Telegram localization helpers."""

from __future__ import annotations

import pytest

from metax.frameworks_and_drivers.telegram_bot.localization import localized_category_name


@pytest.mark.parametrize(
    ("language_code", "expected"),
    [
        ("hy", "Կաթնամթերք"),
        ("ru", "Молочное"),
        ("en", "Dairy"),
        ("fr", "Dairy"),  # unsupported language falls back to the English name
    ],
)
def test_localized_category_name(language_code: str, expected: str) -> None:
    assert (
        localized_category_name("Dairy", "Կաթնամթերք", "Молочное", language_code) == expected
    )


def test_localized_category_name_falls_back_when_translation_missing() -> None:
    # Armenian requested but only the English name exists -> English fallback.
    assert localized_category_name("Dairy", "", "", "hy") == "Dairy"
