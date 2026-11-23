"""Command handlers: /start, /help, /search, /categories — plus the shared free-text search entry point."""

from __future__ import annotations

import contextlib
import logging

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReplyKeyboardRemove

from metax.frameworks_and_drivers.telegram_bot.keyboards import (
    categories_keyboard,
    clamp_query,
    language_keyboard,
    stores_keyboard,
)
from metax.frameworks_and_drivers.telegram_bot.localization import t
from metax.frameworks_and_drivers.telegram_bot.queries import load_categories, load_retailers
from metax.frameworks_and_drivers.telegram_bot.result_pages import build_search_page, send_result_page
from metax.frameworks_and_drivers.telegram_bot.user_state import session_for

logger = logging.getLogger(__name__)

router = Router()

# Labels of the reply keyboard (the button panel under the input field) that V1 of the bot showed.
# Telegram keeps a reply keyboard on the user's device until the bot explicitly removes it, so users
# who met V1 still have these buttons; tapping one sends its label as plain text, which would
# otherwise be searched as a product name ("nothing found"). They are routed to their real actions
# and the stale keyboard is removed.
_LEGACY_CATEGORIES_BUTTON = "📂 Категории"
_LEGACY_HELP_BUTTON = "ℹ️ Помощь"  # noqa: RUF001 — exact label of the V1 button


async def remove_legacy_reply_keyboard(message: Message) -> None:
    """Remove a stale V1 reply keyboard from the user's chat.

    ``ReplyKeyboardRemove`` can only ride on a sent message, so a throwaway message carries it and is
    deleted right away; the client has already dropped the keyboard by then.
    """
    carrier = await message.answer("⌨️", reply_markup=ReplyKeyboardRemove())
    with contextlib.suppress(TelegramBadRequest):
        await carrier.delete()


async def run_search(message: Message, raw_query: str) -> None:
    session = session_for(message.from_user.id if message.from_user else None)
    lang = session.language
    if not raw_query.strip():
        await message.answer(f"{t(lang, 'search_prompt')}\n{t(lang, 'search_example')}", parse_mode=ParseMode.HTML)
        return

    # The clamped query is what is searched and carried in the pagination buttons, so every page of
    # the result set is computed from the same text.
    query = clamp_query(raw_query)
    # Remember the query so changing the retailer filter can re-run it.
    session.enter_search(query)
    status = await message.answer(t(lang, "search_loading"))

    try:
        page = await build_search_page(session, query)
    except Exception:
        logger.exception("Search failed for query %r", query)
        await status.edit_text(t(lang, "search_error"))
        return

    if page.is_empty:
        # Keep the retailer filter controls under "nothing found": a filter set earlier is otherwise
        # invisible here and the product looks missing everywhere.
        await status.edit_text(page.empty_text, parse_mode=ParseMode.HTML, reply_markup=page.empty_keyboard)
        return
    await status.delete()
    await send_result_page(message, page, lang)


async def show_categories(message: Message) -> None:
    lang = session_for(message.from_user.id if message.from_user else None).language
    categories = await load_categories(lang)
    if not categories:
        await message.answer(t(lang, "categories_none"))
        return
    await message.answer(t(lang, "categories_title"), reply_markup=categories_keyboard(categories))


async def show_stores(message: Message) -> None:
    lang = session_for(message.from_user.id if message.from_user else None).language
    retailers = await load_retailers()
    if not retailers:
        await message.answer(t(lang, "stores_none"))
        return
    await message.answer(t(lang, "stores_title"), reply_markup=stores_keyboard(retailers))


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    lang = session_for(message.from_user.id if message.from_user else None).language
    await remove_legacy_reply_keyboard(message)
    await message.answer(t(lang, "choose_language"), parse_mode=ParseMode.HTML, reply_markup=language_keyboard())


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    lang = session_for(message.from_user.id if message.from_user else None).language
    await message.answer(t(lang, "help"), parse_mode=ParseMode.HTML)


@router.message(Command("search"))
async def search_handler(message: Message) -> None:
    if message.text is None:
        return
    parts = message.text.split(maxsplit=1)
    await run_search(message, parts[1] if len(parts) >= 2 else "")


@router.message(Command("stores"))
async def stores_handler(message: Message) -> None:
    await show_stores(message)


@router.message(Command("categories"))
async def categories_handler(message: Message) -> None:
    await show_categories(message)


@router.message(F.text == _LEGACY_CATEGORIES_BUTTON)
async def legacy_categories_button_handler(message: Message) -> None:
    await remove_legacy_reply_keyboard(message)
    await show_categories(message)


@router.message(F.text == _LEGACY_HELP_BUTTON)
async def legacy_help_button_handler(message: Message) -> None:
    await remove_legacy_reply_keyboard(message)
    await help_handler(message)
