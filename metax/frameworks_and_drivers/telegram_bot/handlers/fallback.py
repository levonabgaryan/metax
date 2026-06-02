"""Catch-all handler: reply-keyboard buttons and free-text search."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.types import Message

from metax.frameworks_and_drivers.telegram_bot.handlers.commands import (
    categories_handler,
    help_handler,
    run_search,
)
from metax.frameworks_and_drivers.telegram_bot.keyboards import CATEGORIES_BTN, HELP_BTN

router = Router()


@router.message(F.text == CATEGORIES_BTN)
async def menu_categories(message: Message) -> None:
    await categories_handler(message)


@router.message(F.text == HELP_BTN)
async def menu_help(message: Message) -> None:
    await help_handler(message)


@router.message(F.text)
async def free_text_search(message: Message) -> None:
    await run_search(message, message.text or "")


@router.message()
async def unsupported_handler(message: Message) -> None:
    await message.answer(
        "Напишите название товара для поиска.",
        parse_mode=ParseMode.HTML,
    )
