"""Command handlers: /start, /help, /search, /categories — plus the shared free-text search entry point."""

from __future__ import annotations

import html
import logging

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from metax.frameworks_and_drivers.telegram_bot.keyboards import categories_keyboard, clamp_query, language_keyboard
from metax.frameworks_and_drivers.telegram_bot.localization import t
from metax.frameworks_and_drivers.telegram_bot.queries import load_categories
from metax.frameworks_and_drivers.telegram_bot.result_pages import build_search_page, send_result_page
from metax.frameworks_and_drivers.telegram_bot.user_state import session_for

logger = logging.getLogger(__name__)

router = Router()


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
        await status.edit_text(t(lang, "search_empty", query=html.escape(query)), parse_mode=ParseMode.HTML)
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


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    lang = session_for(message.from_user.id if message.from_user else None).language
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


@router.message(Command("categories"))
async def categories_handler(message: Message) -> None:
    await show_categories(message)
