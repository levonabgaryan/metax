"""Inline keyboard builders and callback data types."""

from __future__ import annotations

from collections.abc import Sequence

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from metax.frameworks_and_drivers.telegram_bot.localization import (
    language_buttons,
    retailer_display_name,
    t,
)

PAGE_SIZE = 5

# Telegram caps callback_data at 64 bytes. A packed ``SearchNavCB`` is ``sn:<query>:<offset>``, so the
# prefix, two separators and a generous 6-digit offset leave 55 bytes; keep a little headroom.
_QUERY_BYTE_BUDGET = 48
# aiogram's CallbackData separator; a value containing it cannot be packed.
_CALLBACK_SEPARATOR = ":"


class SearchNavCB(CallbackData, prefix="sn"):
    query: str
    offset: int


class CategoryBrowseCB(CallbackData, prefix="cb"):
    category_uuid: str
    offset: int


class OpenCategoriesCB(CallbackData, prefix="bck"):
    pass


class LanguageSelectCB(CallbackData, prefix="lang"):
    language_code: str


# Two separate store features, kept apart on purpose so neither hijacks the other:
#   * Narrowing (🔎, ``RetailerFilter*`` / ``RetailerSelect`` / ``RetailerClear``): limits searches and
#     category browse to one store. Shown under result pages; changing it re-runs the current view.
#   * Store browse (🏪, ``OpenStores`` / ``StoreBrowse``): opens one store's discount list. It never
#     touches the narrowing or the last search.
class RetailerFilterMenuCB(CallbackData, prefix="rfm"):
    pass


class RetailerSelectCB(CallbackData, prefix="rfs"):
    retailer_uuid: str


class RetailerClearCB(CallbackData, prefix="rfc"):
    pass


class OpenStoresCB(CallbackData, prefix="sto"):
    pass


class StoreBrowseCB(CallbackData, prefix="sb"):
    retailer_uuid: str
    offset: int


class StoreSearchCB(CallbackData, prefix="ss"):
    """From a store's page: narrow the next typed search to that store."""

    retailer_uuid: str


def clamp_query(query: str) -> str:
    """Make a search query safe to carry in ``SearchNavCB``.

    Replaces the callback separator (``:`` would make packing raise) and trims the query to the byte
    budget without splitting a multi-byte character. The clamped form is what gets searched, so every
    page of a result set is computed from the same query.

    Returns:
        The callback-safe query.
    """
    cleaned = " ".join(query.replace(_CALLBACK_SEPARATOR, " ").split())
    encoded = cleaned.encode("utf-8")
    if len(encoded) <= _QUERY_BYTE_BUDGET:
        return cleaned
    return encoded[:_QUERY_BYTE_BUDGET].decode("utf-8", errors="ignore").rstrip()


def language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, language_code in language_buttons():
        builder.button(text=label, callback_data=LanguageSelectCB(language_code=language_code))
    builder.adjust(3)
    return builder.as_markup()


def _filter_control_buttons(
    language_code: str, selected_retailer_name: str | None
) -> list[tuple[str, CallbackData]]:
    """Search-narrowing controls: a status button that opens the store picker, plus Clear when narrowed.

    Returns:
        ``(label, callback_data)`` pairs, one button per row.
    """
    if selected_retailer_name is None:
        status = f"🔎 {t(language_code, 'current_filter')}: {t(language_code, 'current_filter_none')}"
        return [(status, RetailerFilterMenuCB())]
    status = f"🔎 {t(language_code, 'current_filter')}: {retailer_display_name(selected_retailer_name)}"
    return [
        (status, RetailerFilterMenuCB()),
        (f"✖ {t(language_code, 'clear_retailer_filter')}", RetailerClearCB()),
    ]


def _menu_buttons(language_code: str) -> list[tuple[str, CallbackData]]:
    """The two browse entry points, shown side by side at the bottom of most keyboards.

    Returns:
        ``(label, callback_data)`` pairs for Stores and Categories.
    """
    return [
        (t(language_code, "browse_stores"), OpenStoresCB()),
        (t(language_code, "browse_categories"), OpenCategoriesCB()),
    ]


def _build(rows: Sequence[Sequence[tuple[str, CallbackData]]]) -> InlineKeyboardMarkup:
    """Lay buttons out one input row per keyboard row, skipping empty rows (e.g. no prev/next).

    Returns:
        The inline keyboard.
    """
    builder = InlineKeyboardBuilder()
    for row in rows:
        for text, callback_data in row:
            builder.button(text=text, callback_data=callback_data)
    builder.adjust(*[len(row) for row in rows if row])
    return builder.as_markup()


def main_menu_keyboard(
    *,
    language_code: str,
    selected_retailer_name: str | None = None,
) -> InlineKeyboardMarkup:
    """Intro/menu keyboard: Stores + Categories, and the search narrowing only while it is active.

    Returns:
        The inline keyboard.
    """
    filter_rows = [[button] for button in _filter_control_buttons(language_code, selected_retailer_name)]
    return _build([*(filter_rows if selected_retailer_name is not None else []), _menu_buttons(language_code)])


def stores_keyboard(retailers: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    """Store picker for browsing: each button opens that store's discounts.

    Returns:
        The inline keyboard, two stores per row.
    """
    builder = InlineKeyboardBuilder()
    for retailer_uuid, retailer_name in retailers:
        builder.button(
            text=f"🏪 {retailer_display_name(retailer_name)}",
            callback_data=StoreBrowseCB(retailer_uuid=retailer_uuid, offset=0),
        )
    builder.adjust(2)
    return builder.as_markup()


def retailer_selection_keyboard(
    retailers: list[tuple[str, str]],
    *,
    language_code: str,
    selected_uuid: str | None = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # "All shops" doubles as the clear action; mark it active when no retailer is selected.
    all_mark = "✓ " if selected_uuid is None else ""
    builder.button(
        text=f"{all_mark}{t(language_code, 'clear_retailer_filter')}",
        callback_data=RetailerClearCB(),
    )
    for retailer_uuid, retailer_name in retailers:
        mark = "✓ " if retailer_uuid == selected_uuid else "🏪 "
        builder.button(
            text=f"{mark}{retailer_display_name(retailer_name)}",
            callback_data=RetailerSelectCB(retailer_uuid=retailer_uuid),
        )
    builder.adjust(1, 2)
    return builder.as_markup()


def search_result_keyboard(
    query: str,
    offset: int,
    total: int,
    *,
    language_code: str,
    selected_retailer_name: str | None = None,
) -> InlineKeyboardMarkup:
    return _results_keyboard(
        prev_page=SearchNavCB(query=query, offset=max(0, offset - PAGE_SIZE)) if offset > 0 else None,
        next_page=SearchNavCB(query=query, offset=offset + PAGE_SIZE) if offset + PAGE_SIZE < total else None,
        language_code=language_code,
        selected_retailer_name=selected_retailer_name,
    )


def empty_result_keyboard(
    *, language_code: str, selected_retailer_name: str | None = None
) -> InlineKeyboardMarkup:
    """Keyboard under a "nothing found" search or category: narrowing controls and the browse menu.

    Without it an empty result narrowed to one store reads as "this product doesn't exist anywhere";
    showing the active narrowing (and a one-tap way to clear it) makes it visible.

    Returns:
        The inline keyboard.
    """
    return _results_keyboard(
        prev_page=None,
        next_page=None,
        language_code=language_code,
        selected_retailer_name=selected_retailer_name,
    )


def categories_keyboard(categories: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat_uuid, cat_name in categories:
        builder.button(
            text=cat_name,
            callback_data=CategoryBrowseCB(category_uuid=cat_uuid, offset=0),
        )
    builder.adjust(2)
    return builder.as_markup()


def category_nav_keyboard(
    category_uuid: str,
    offset: int,
    total: int,
    *,
    language_code: str,
    selected_retailer_name: str | None = None,
) -> InlineKeyboardMarkup:
    return _results_keyboard(
        prev_page=(
            CategoryBrowseCB(category_uuid=category_uuid, offset=max(0, offset - PAGE_SIZE))
            if offset > 0
            else None
        ),
        next_page=(
            CategoryBrowseCB(category_uuid=category_uuid, offset=offset + PAGE_SIZE)
            if offset + PAGE_SIZE < total
            else None
        ),
        language_code=language_code,
        selected_retailer_name=selected_retailer_name,
    )


def store_nav_keyboard(
    retailer_uuid: str,
    retailer_name: str,
    offset: int,
    total: int,
    *,
    language_code: str,
) -> InlineKeyboardMarkup:
    """Keyboard under a store's discount page: prev/next, "search in this store", then the browse menu.

    No narrowing controls here: browsing a store is its own view, independent of the search narrowing.

    Returns:
        The inline keyboard.
    """
    nav = [
        (t(language_code, label_key), callback_data)
        for label_key, callback_data in (
            (
                "back",
                StoreBrowseCB(retailer_uuid=retailer_uuid, offset=max(0, offset - PAGE_SIZE))
                if offset > 0
                else None,
            ),
            (
                "next",
                StoreBrowseCB(retailer_uuid=retailer_uuid, offset=offset + PAGE_SIZE)
                if offset + PAGE_SIZE < total
                else None,
            ),
        )
        if callback_data is not None
    ]
    search_here = (
        t(language_code, "search_in_store", retailer=retailer_display_name(retailer_name)),
        StoreSearchCB(retailer_uuid=retailer_uuid),
    )
    return _build([nav, [search_here], _menu_buttons(language_code)])


def _results_keyboard(
    *,
    prev_page: CallbackData | None,
    next_page: CallbackData | None,
    language_code: str,
    selected_retailer_name: str | None,
) -> InlineKeyboardMarkup:
    """Keyboard under a search or category page: prev/next, the search narrowing, then the browse menu.

    Returns:
        The inline keyboard.
    """
    nav = [
        (t(language_code, label_key), callback_data)
        for label_key, callback_data in (("back", prev_page), ("next", next_page))
        if callback_data is not None
    ]
    filter_rows = [[button] for button in _filter_control_buttons(language_code, selected_retailer_name)]
    return _build([nav, *filter_rows, _menu_buttons(language_code)])
