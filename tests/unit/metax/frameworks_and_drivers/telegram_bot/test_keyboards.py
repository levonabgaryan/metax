"""Unit tests for Telegram keyboard helpers."""

from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup

from metax.frameworks_and_drivers.telegram_bot.keyboards import (
    RetailerClearCB,
    RetailerFilterMenuCB,
    SearchNavCB,
    StoreBrowseCB,
    StoreSearchCB,
    clamp_query,
    empty_result_keyboard,
    main_menu_keyboard,
    search_result_keyboard,
    store_nav_keyboard,
    stores_keyboard,
)


def test_clamp_query_replaces_callback_separator_so_the_query_can_be_packed() -> None:
    # given: ':' is aiogram's CallbackData separator and would make packing raise
    query = clamp_query("cola:0.5")

    # when / then
    assert query == "cola 0.5"
    SearchNavCB(query=query, offset=0).pack()


def test_clamp_query_keeps_long_multibyte_queries_within_callback_limit() -> None:
    # given: Armenian letters are 2 bytes each in UTF-8
    query = clamp_query("կաթնաշոռ " * 10)

    # when
    packed = SearchNavCB(query=query, offset=99_995).pack()

    # then: Telegram's 64-byte callback_data limit holds and no character was split
    assert len(packed.encode("utf-8")) <= 64
    assert "\ufffd" not in query


def test_search_result_keyboard_has_prev_and_next_in_the_middle_of_results() -> None:
    keyboard = search_result_keyboard("milk", offset=5, total=20, language_code="en")

    nav_row = keyboard.inline_keyboard[0]
    assert [button.text for button in nav_row] == ["← Back", "Next →"]


def test_empty_result_keyboard_shows_active_retailer_filter_with_clear_button() -> None:
    # given: a search came back empty while the result set was narrowed to one store
    keyboard = empty_result_keyboard(language_code="en", selected_retailer_name="sas-am")

    # then: the filter is named and can be cleared in one tap, so "nothing found" is not misread
    labels = [button.text for row in keyboard.inline_keyboard for button in row]
    assert "🔎 Search in: SAS" in labels
    assert "✖ Show all retailers" in labels
    clear_button = next(b for row in keyboard.inline_keyboard for b in row if b.text == "✖ Show all retailers")
    assert clear_button.callback_data == RetailerClearCB().pack()


def test_empty_result_keyboard_without_filter_has_no_clear_button_or_nav() -> None:
    keyboard = empty_result_keyboard(language_code="en")

    labels = [button.text for row in keyboard.inline_keyboard for button in row]
    assert labels == ["🔎 Search in: all stores", "🏪 Stores", "📂 Categories"]


_ROUGE_UUID = "00000000-0000-0000-0000-00000000000a"


def _callbacks(markup: InlineKeyboardMarkup) -> list[str]:
    return [button.callback_data for row in markup.inline_keyboard for button in row]


def test_store_picker_buttons_browse_the_store_instead_of_narrowing_the_search() -> None:
    # given: the user searched "panir" earlier and now opens the store list
    keyboard = stores_keyboard([(_ROUGE_UUID, "rouge-am")])

    # then: picking ROUGE opens ROUGE's discounts — it is not the narrowing callback
    button = keyboard.inline_keyboard[0][0]
    assert button.text == "🏪 ROUGE"
    assert button.callback_data == StoreBrowseCB(retailer_uuid=_ROUGE_UUID, offset=0).pack()


def test_store_page_keyboard_offers_search_in_store_and_no_narrowing_controls() -> None:
    keyboard = store_nav_keyboard(_ROUGE_UUID, "rouge-am", offset=0, total=12, language_code="en")

    labels = [button.text for row in keyboard.inline_keyboard for button in row]
    assert labels == ["Next →", "🔍 Search in ROUGE", "🏪 Stores", "📂 Categories"]
    assert StoreSearchCB(retailer_uuid=_ROUGE_UUID).pack() in _callbacks(keyboard)
    assert RetailerFilterMenuCB().pack() not in _callbacks(keyboard)


def test_store_page_keyboard_pages_within_the_store() -> None:
    keyboard = store_nav_keyboard(_ROUGE_UUID, "rouge-am", offset=5, total=12, language_code="en")

    nav = keyboard.inline_keyboard[0]
    assert [b.callback_data for b in nav] == [
        StoreBrowseCB(retailer_uuid=_ROUGE_UUID, offset=0).pack(),
        StoreBrowseCB(retailer_uuid=_ROUGE_UUID, offset=10).pack(),
    ]


def test_search_results_keep_narrowing_and_stores_as_separate_buttons() -> None:
    keyboard = search_result_keyboard("panir", offset=0, total=3, language_code="en")

    labels = [button.text for row in keyboard.inline_keyboard for button in row]
    assert labels == ["🔎 Search in: all stores", "🏪 Stores", "📂 Categories"]


def test_main_menu_shows_narrowing_only_while_active() -> None:
    plain = main_menu_keyboard(language_code="en")
    narrowed = main_menu_keyboard(language_code="en", selected_retailer_name="rouge-am")

    assert [b.text for row in plain.inline_keyboard for b in row] == ["🏪 Stores", "📂 Categories"]
    assert [b.text for row in narrowed.inline_keyboard for b in row] == [
        "🔎 Search in: ROUGE",
        "✖ Show all retailers",
        "🏪 Stores",
        "📂 Categories",
    ]
