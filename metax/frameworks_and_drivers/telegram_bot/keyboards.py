"""Inline keyboard builders and callback data types."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from metax.frameworks_and_drivers.telegram_bot.localization import language_buttons, t

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


def retailer_filter_keyboard(
    *,
    language_code: str,
    selected_retailer_name: str | None = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=(
            f"{t(language_code, 'current_filter')}: {selected_retailer_name}"
            if selected_retailer_name is not None
            else f"{t(language_code, 'current_filter')}: {t(language_code, 'current_filter_none')}"
        ),
        callback_data=RetailerFilterMenuCB(),
    )
    builder.button(text=t(language_code, "filter_by_retailer"), callback_data=RetailerFilterMenuCB())
    if selected_retailer_name is not None:
        builder.button(text=t(language_code, "clear_retailer_filter"), callback_data=RetailerClearCB())
    builder.adjust(1, 2)
    return builder.as_markup()


def retailer_selection_keyboard(
    retailers: list[tuple[str, str]],
    *,
    language_code: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t(language_code, "clear_retailer_filter"), callback_data=RetailerClearCB())
    for retailer_uuid, retailer_name in retailers:
        builder.button(
            text=retailer_name,
            callback_data=RetailerSelectCB(retailer_uuid=retailer_uuid),
        )
    builder.adjust(2)
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
    if has_prev or has_next:
        builder.adjust(2)

    filter_row = []
    if selected_retailer_name is None:
        filter_row.append((f"{t(language_code, 'current_filter')}: {t(language_code, 'current_filter_none')}", RetailerFilterMenuCB()))
        filter_row.append((t(language_code, "filter_by_retailer"), RetailerFilterMenuCB()))
    else:
        filter_row.append((f"{t(language_code, 'current_filter')}: {selected_retailer_name}", RetailerFilterMenuCB()))
        filter_row.append((t(language_code, "clear_retailer_filter"), RetailerClearCB()))

    for text, callback_data in filter_row:
        builder.button(text=text, callback_data=callback_data)
    if filter_row:
        builder.adjust(2, 2)

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
