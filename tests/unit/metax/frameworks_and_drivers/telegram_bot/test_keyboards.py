"""Unit tests for Telegram keyboard helpers."""

from __future__ import annotations

from metax.frameworks_and_drivers.telegram_bot.keyboards import SearchNavCB, clamp_query, search_result_keyboard


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
