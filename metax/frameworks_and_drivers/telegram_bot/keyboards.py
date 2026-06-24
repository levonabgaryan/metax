"""Inline keyboard builders and callback data types."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from metax.frameworks_and_drivers.telegram_bot.localization import (
    language_buttons,
    retailer_display_name,
    t,
)

PAGE_SIZE = 5

# Telegram caps callback_data at 64 bytes.
_QUERY_BYTE_BUDGET = 32
_CATEGORY_NAME_BYTE_BUDGET = 18

CATEGORIES_BTN = "📂 Категории"
HELP_BTN = "ℹ️ Помощь"


class SearchNavCB(CallbackData, prefix="sn"):
    query: str
    offset: int


class CategoryBrowseCB(CallbackData, prefix="cb"):
    category_uuid: str
    category_name: str
    offset: int


class BackToCategoriesCB(CallbackData, prefix="bck"):
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
    encoded = query.encode("utf-8")
    if len(encoded) <= _QUERY_BYTE_BUDGET:
        return query
    return encoded[:_QUERY_BYTE_BUDGET].decode("utf-8", errors="ignore")


def clamp_category_name(name: str) -> str:
    encoded = name.encode("utf-8")
    if len(encoded) <= _CATEGORY_NAME_BYTE_BUDGET:
        return name
    return encoded[:_CATEGORY_NAME_BYTE_BUDGET].decode("utf-8", errors="ignore")


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CATEGORIES_BTN), KeyboardButton(text=HELP_BTN)]],
        resize_keyboard=True,
        input_field_placeholder="Введите название товара для поиска…",
    )


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
) -> InlineKeyboardMarkup | None:
    builder = InlineKeyboardBuilder()
    has_prev = offset > 0
    has_next = offset + PAGE_SIZE < total
    nav_count = has_prev + has_next
    if has_prev:
        builder.button(
            text=t(language_code, "back"),
            callback_data=SearchNavCB(query=query, offset=max(0, offset - PAGE_SIZE)),
        )
    if has_next:
        builder.button(
            text=t(language_code, "next"),
            callback_data=SearchNavCB(query=query, offset=offset + PAGE_SIZE),
        )

    filter_buttons = _filter_control_buttons(language_code, selected_retailer_name)
    for text, callback_data in filter_buttons:
        builder.button(text=text, callback_data=callback_data)

    # Nav buttons share one row; each filter control sits on its own row below.
    sizes = ([nav_count] if nav_count else []) + [1] * len(filter_buttons)
    builder.adjust(*sizes)
    return builder.as_markup()


def search_nav_keyboard(query: str, offset: int, total: int) -> InlineKeyboardMarkup | None:
    has_prev = offset > 0
    has_next = offset + PAGE_SIZE < total
    if not has_prev and not has_next:
        return None

    builder = InlineKeyboardBuilder()
    if has_prev:
        builder.button(
            text="← Назад",
            callback_data=SearchNavCB(query=query, offset=max(0, offset - PAGE_SIZE)),
        )
    if has_next:
        builder.button(
            text="Далее →",
            callback_data=SearchNavCB(query=query, offset=offset + PAGE_SIZE),
        )
    builder.adjust(2)
    return builder.as_markup()


def categories_keyboard(categories: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat_uuid, cat_name in categories:
        builder.button(
            text=cat_name,
            callback_data=CategoryBrowseCB(
                category_uuid=cat_uuid,
                category_name=clamp_category_name(cat_name),
                offset=0,
            ),
        )
    builder.adjust(2)
    return builder.as_markup()


def category_nav_keyboard(
    category_uuid: str,
    category_name: str,
    offset: int,
    total: int,
) -> InlineKeyboardMarkup:
    has_prev = offset > 0
    has_next = offset + PAGE_SIZE < total
    nav_count = 0

    builder = InlineKeyboardBuilder()
    if has_prev:
        builder.button(
            text="← Назад",
            callback_data=CategoryBrowseCB(
                category_uuid=category_uuid,
                category_name=category_name,
                offset=max(0, offset - PAGE_SIZE),
            ),
        )
        nav_count += 1
    if has_next:
        builder.button(
            text="Далее →",
            callback_data=CategoryBrowseCB(
                category_uuid=category_uuid,
                category_name=category_name,
                offset=offset + PAGE_SIZE,
            ),
        )
        nav_count += 1
    builder.button(text="📂 К категориям", callback_data=BackToCategoriesCB())
    builder.adjust(nav_count or 1, 1)
    return builder.as_markup()
