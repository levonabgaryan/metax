"""Catch-all handler: free-text search."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.types import Message

from metax.frameworks_and_drivers.telegram_bot.handlers.commands import run_search
from metax.frameworks_and_drivers.telegram_bot.localization import t
from metax.frameworks_and_drivers.telegram_bot.user_state import session_for

router = Router()


@router.message(F.text)
async def free_text_search(message: Message) -> None:
    await run_search(message, message.text or "")


@router.message()
async def unsupported_handler(message: Message) -> None:
    lang = session_for(message.from_user.id if message.from_user else None).language
    await message.answer(t(lang, "unsupported"), parse_mode=ParseMode.HTML)
