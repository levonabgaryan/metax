import asyncio
import logging
import os
import sys
from pathlib import Path

from metax_bootstrap import METAX_LIFESPAN_MANAGER

logger = logging.getLogger(__name__)


def _read_telegram_token() -> str | None:
    """Read TELEGRAM_BOT_TOKEN from os.environ first, then fall back to .env.

    DevConfigs does not read .env at all, so pydantic never sees values from
    that file. We mirror the same peek-at-.env approach used by
    _read_env_name_from_dotenv() in metax_configs.py.

    Returns:
        The bot token if found in the environment or .env file, otherwise ``None``.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if token:
        return token
    env_file = Path(__file__).resolve().parent / ".env"
    if not env_file.exists():
        return None
    from dotenv import dotenv_values

    return dotenv_values(str(env_file)).get("TELEGRAM_BOT_TOKEN") or None


async def _run() -> None:
    token = _read_telegram_token()
    if not token:
        msg = "TELEGRAM_BOT_TOKEN is not configured. Set it in .env or as an environment variable."
        raise RuntimeError(msg)

    METAX_LIFESPAN_MANAGER.configure_logger()
    METAX_LIFESPAN_MANAGER.configure_django_app()
    await METAX_LIFESPAN_MANAGER.init_metax_container_resources()

    from metax.frameworks_and_drivers.telegram_bot.bot import run_bot

    try:
        await run_bot(token=token)
    finally:
        await METAX_LIFESPAN_MANAGER.shutdown_metax_container_resources()


if __name__ == "__main__":
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        sys.exit(0)
