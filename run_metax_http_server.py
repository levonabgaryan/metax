from __future__ import annotations

import asyncio
import logging
import sys

from config_ import DevConfigs, metax_configs
from entrypoint import run_entrypoint
from metax.frameworks_and_drivers.gunicorn.run_gunicorn_server import run_django_gunicorn_server
from metax.frameworks_and_drivers.uvicorn.run_uvicorn_server import run_django_uvicorn_server
from metax_logger.logger import init_logger

from metax_django_application import create_metax_django_app

logger = logging.getLogger(__name__)


def run_metax_http_server() -> None:
    init_logger()
    app = create_metax_django_app()
    logger.info("SYSTEM | Application bootstrap started")
    from metax.frameworks_and_drivers.di.metax_container import MetaxContainer, init_resources, shutdown_resources  # noqa: E402

    container: MetaxContainer = app.container  # type: ignore[attr-defined]

    async def startup() -> None:
        await init_resources(container)
        opensearch_client = await container.opensearch_async_client.async_()
        await run_entrypoint(opensearch_client)

    try:
        asyncio.run(startup())
        if isinstance(metax_configs, DevConfigs):
            run_django_uvicorn_server()
        else:
            asyncio.run(run_django_gunicorn_server())
    except KeyboardInterrupt:
        logger.warning("SHUTDOWN | Stop signal received. Cleaning up...")
    except Exception as e:
        logger.critical("RUNTIME | Unhandled Exception during startup: %s", e, exc_info=True)
        sys.exit(1)
    finally:
        logger.info("SHUTDOWN | Releasing resources...")
        asyncio.run(shutdown_resources(container))
        logger.info("SHUTDOWN | Metax shut down!")


if __name__ == "__main__":
    try:
        run_metax_http_server()
    except KeyboardInterrupt:
        pass
