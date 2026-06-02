"""Inline keyboard builders and callback data types."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

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
