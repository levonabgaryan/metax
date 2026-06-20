"""Aiogram middleware."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject, User

from metax.frameworks_and_drivers.telegram_bot.localization import get_user_language, t


class ThrottleMiddleware(BaseMiddleware):
    """Prevent a single user from flooding the bot with messages.

    Only message events are throttled; callback queries (button presses) are
    intentionally exempt so that pagination still feels responsive.
    """

    def __init__(self, rate_seconds: float = 1.0) -> None:
        self._last_call: dict[int, float] = {}
        self._rate = rate_seconds

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            user: User | None = data.get("event_from_user")
            if user is not None:
                now = time.monotonic()
                if now - self._last_call.get(user.id, 0.0) < self._rate:
                    await event.answer(t(get_user_language(user.id), "throttle"))
                    return None
                self._last_call[user.id] = now
        return await handler(event, data)
