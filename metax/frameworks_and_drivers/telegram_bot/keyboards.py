"""Inline keyboard builders and callback data types."""

from __future__ import annotations

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


class RetailerFilterMenuCB(CallbackData, prefix="rfm"):
    pass


class RetailerSelectCB(CallbackData, prefix="rfs"):
    retailer_uuid: str


class RetailerClearCB(CallbackData, prefix="rfc"):
    pass


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
    """Retailer-filter controls: one status button that opens the menu, plus Clear when a filter is active.

    Returns:
        ``(label, callback_data)`` pairs, one button per row.
    """
    if selected_retailer_name is None:
        status = f"🏪 {t(language_code, 'current_filter')}: {t(language_code, 'current_filter_none')}"
        return [(status, RetailerFilterMenuCB())]
    status = f"🏪 {t(language_code, 'current_filter')}: {retailer_display_name(selected_retailer_name)}"
    return [
        (status, RetailerFilterMenuCB()),
        (f"✖ {t(language_code, 'clear_retailer_filter')}", RetailerClearCB()),
    ]


def retailer_filter_keyboard(
    *,
    language_code: str,
    selected_retailer_name: str | None = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for text, callback_data in _filter_control_buttons(language_code, selected_retailer_name):
        builder.button(text=text, callback_data=callback_data)
    builder.button(text=t(language_code, "browse_categories"), callback_data=OpenCategoriesCB())
    builder.adjust(1)
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


def _results_keyboard(
    *,
    prev_page: CallbackData | None,
    next_page: CallbackData | None,
    language_code: str,
    selected_retailer_name: str | None,
) -> InlineKeyboardMarkup:
    """Keyboard under a result page: prev/next on one row, then the retailer filter and categories.

    Shared by search results and category browse, so a store filter can be applied (or cleared)
    from either view without leaving it.

    Returns:
        The inline keyboard.
    """
    builder = InlineKeyboardBuilder()
    nav_buttons = [
        (t(language_code, label_key), callback_data)
        for label_key, callback_data in (("back", prev_page), ("next", next_page))
        if callback_data is not None
    ]
    filter_buttons = _filter_control_buttons(language_code, selected_retailer_name)
    for text, callback_data in [*nav_buttons, *filter_buttons]:
        builder.button(text=text, callback_data=callback_data)
    builder.button(text=t(language_code, "browse_categories"), callback_data=OpenCategoriesCB())

    # Nav buttons share one row; each filter control and the categories shortcut sit on their own row.
    sizes = ([len(nav_buttons)] if nav_buttons else []) + [1] * len(filter_buttons) + [1]
    builder.adjust(*sizes)
    return builder.as_markup()
