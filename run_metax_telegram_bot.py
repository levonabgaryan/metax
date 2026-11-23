import asyncio
import logging
import sys

from metax_bootstrap import METAX_CONFIGS, METAX_LIFESPAN_MANAGER

logger = logging.getLogger(__name__)


async def _run() -> None:
    # Same source as the taskiq worker's crawl digest (``DevConfigs`` falls back to ``.env``).
    token = METAX_CONFIGS.telegram_bot_token
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
