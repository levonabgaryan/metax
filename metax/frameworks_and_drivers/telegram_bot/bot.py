"""Telegram bot: dispatcher setup and entry point."""

from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from metax.frameworks_and_drivers.telegram_bot.handlers import callbacks, commands, fallback
from metax.frameworks_and_drivers.telegram_bot.localization import SUPPORTED_LANGUAGES, bot_commands_for_language
from metax.frameworks_and_drivers.telegram_bot.middleware import ThrottleMiddleware

logger = logging.getLogger(__name__)


async def run_bot(token: str) -> None:
    """Start the Telegram bot in long-polling mode."""
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.message.middleware(ThrottleMiddleware(rate_seconds=1.0))

    # Order matters: specific routers before the catch-all fallback.
    dp.include_router(commands.router)
    dp.include_router(callbacks.router)
    dp.include_router(fallback.router)

    for language_code in SUPPORTED_LANGUAGES:
        await bot.set_my_commands(bot_commands_for_language(language_code), language_code=language_code)
    await bot.set_my_commands(bot_commands_for_language("en"))

    logger.info("STARTUP | Task: Telegram Bot | Status: RUNNING")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        logger.info("SHUTDOWN | Task: Telegram Bot | Status: STOPPED")
