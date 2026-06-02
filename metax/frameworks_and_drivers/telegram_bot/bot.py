"""Telegram bot: dispatcher setup and entry point."""

from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from metax.frameworks_and_drivers.telegram_bot.handlers import callbacks, commands, fallback
from metax.frameworks_and_drivers.telegram_bot.middleware import ThrottleMiddleware

logger = logging.getLogger(__name__)

_BOT_COMMANDS = [
    BotCommand(command="start", description="Запустить бота"),
    BotCommand(command="search", description="Поиск товаров со скидками"),
    BotCommand(command="categories", description="Просмотр по категориям"),
    BotCommand(command="help", description="Справка"),
]


async def run_bot(token: str) -> None:
    """Start the Telegram bot in long-polling mode."""
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.message.middleware(ThrottleMiddleware(rate_seconds=1.0))

    # Order matters: specific routers before the catch-all fallback.
    dp.include_router(commands.router)
    dp.include_router(callbacks.router)
    dp.include_router(fallback.router)

    await bot.set_my_commands(_BOT_COMMANDS)

    logger.info("STARTUP | Task: Telegram Bot | Status: RUNNING")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        logger.info("SHUTDOWN | Task: Telegram Bot | Status: STOPPED")
