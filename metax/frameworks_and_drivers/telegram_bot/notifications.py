"""Out-of-band admin notifications (e.g. the nightly crawl digest).

Sent from the TaskIQ worker, which is a different process from the long-polling bot, so we open a
short-lived ``Bot`` just to deliver the message and close its session. Best-effort by design: a missing
token or a Telegram error never propagates — a failed notification must not fail the crawl job.
"""

from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from metax_bootstrap import METAX_CONFIGS

logger = logging.getLogger(__name__)

# The crawl digest goes to the maintainer's private chat. Hardcoded on purpose — it is operational
# wiring, not per-deployment configuration.
_ADMIN_CHAT_ID = 1623970524  # Arik Baghdasaryan (@arikbaghdasaryan)


async def send_admin_notification(text: str) -> None:
    """Deliver ``text`` (Telegram HTML) to the maintainer; log and swallow any failure."""
    token = METAX_CONFIGS.telegram_bot_token
    if not token:
        logger.warning("Admin notification skipped — TELEGRAM_BOT_TOKEN is not configured")
        return

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    try:
        await bot.send_message(chat_id=_ADMIN_CHAT_ID, text=text)
    except Exception:
        logger.exception("Failed to send admin notification")
    finally:
        await bot.session.close()
