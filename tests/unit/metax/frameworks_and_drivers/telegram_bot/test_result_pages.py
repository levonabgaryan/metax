"""Unit tests for result-page building: the active retailer filter must stay visible."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from metax.frameworks_and_drivers.telegram_bot import result_pages
from metax.frameworks_and_drivers.telegram_bot.keyboards import RetailerClearCB
from metax.frameworks_and_drivers.telegram_bot.user_state import UserSession


@pytest.fixture
def empty_search(monkeypatch: pytest.MonkeyPatch) -> None:
    repository = MagicMock()
    repository.search_by_name = AsyncMock(return_value=([], 0))
    repository.search_by_retailer_uuid = AsyncMock(return_value=([], 0))
    monkeypatch.setattr(result_pages, "read_repository", AsyncMock(return_value=repository))
    retailer = MagicMock()
    retailer.get_name.return_value = "sas-am"
    monkeypatch.setattr(result_pages, "load_retailer", AsyncMock(return_value=retailer))


def _button_callbacks(markup: Any) -> list[str]:
    return [button.callback_data for row in markup.inline_keyboard for button in row]


@pytest.mark.usefixtures("empty_search")
async def test_empty_filtered_search_names_the_filter_and_offers_to_clear_it() -> None:
    # given: the user filtered to SAS earlier, then searched for something SAS doesn't have
    session = UserSession(language="en", retailer_uuid="00000000-0000-0000-0000-000000000001")

    # when
    page = await result_pages.build_search_page(session, "cheese")

    # then
    assert page.is_empty
    assert "SAS" in page.empty_text
    assert "retailer filter is on" in page.empty_text
    assert RetailerClearCB().pack() in _button_callbacks(page.empty_keyboard)


@pytest.mark.usefixtures("empty_search")
async def test_empty_unfiltered_search_keeps_plain_text_and_has_no_clear_button() -> None:
    session = UserSession(language="en")

    page = await result_pages.build_search_page(session, "cheese")

    assert page.empty_text == "🔍 <b>«cheese»</b> — found: 0\n\nNothing matched this query."
    assert RetailerClearCB().pack() not in _button_callbacks(page.empty_keyboard)


@pytest.mark.usefixtures("empty_search")
async def test_filtered_search_header_names_the_retailer() -> None:
    session = UserSession(language="en", retailer_uuid="00000000-0000-0000-0000-000000000001")

    page = await result_pages.build_search_page(session, "milk")

    assert page.header == "🔍 <b>«milk»</b> · 🏪 SAS"


@pytest.mark.parametrize("language", ["en", "ru", "hy"])
@pytest.mark.usefixtures("empty_search")
async def test_filtered_empty_text_exists_in_every_language(language: str) -> None:
    session = UserSession(language=language, retailer_uuid="00000000-0000-0000-0000-000000000001")

    page = await result_pages.build_search_page(session, "x")

    assert "SAS" in page.empty_text


@pytest.mark.usefixtures("empty_search")
async def test_store_page_ignores_and_keeps_the_search_narrowing() -> None:
    # given: the last search was "panir", narrowed to another store
    session = UserSession(language="en", retailer_uuid="00000000-0000-0000-0000-000000000002")
    session.enter_search("panir")

    # when: the user browses a store
    page = await result_pages.build_store_page(session, "00000000-0000-0000-0000-000000000001")

    # then: it is the store's page (not a re-run of "panir"), and the search state is untouched
    assert page.header == "🏪 <b>SAS</b>"
    assert "panir" not in page.empty_text
    assert session.last_query == "panir"
    assert session.retailer_uuid == "00000000-0000-0000-0000-000000000002"
