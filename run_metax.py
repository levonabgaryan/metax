from __future__ import annotations

import asyncio
import logging
import os
import sys

from config_ import metax_configs
from entrypoint import run_entrypoint
from logger.logger import init_logger

from metax_django_application import create_metax_django_app

logger = logging.getLogger(__name__)


async def run_django_uvicorn_server() -> None:
    project_root_ = metax_configs.project_root_pythonpath
    django_path_ = metax_configs.django_dir
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(project_root_), str(django_path_)])
    env["DJANGO_SETTINGS_MODULE"] = "django_framework.settings"

    host = metax_configs.django_host
    port = metax_configs.django_port

    if env.get("ENV") == "dev":
        command = [
            "-m",
            "uvicorn",
            "django_framework.asgi:application",
            "--host",
            host,
            "--port",
            str(port),
            "--reload",
            "--reload-dir",
            str(project_root_),
        ]
    else:
        command = [
            "-m",
            "gunicorn",
            "django_framework.asgi:application",
            "-w",
            "2",
            "-k",
            "uvicorn.workers.UvicornWorker",
            "-b",
            f"{host}:{port}",
        ]

    process = await asyncio.create_subprocess_exec(sys.executable, *command, cwd=metax_configs.django_dir, env=env)

    logger.info("[STARTUP] | Task: Web Server | Status: RUNNING | Address: http://%s:%s", host, port)

    try:
        await process.wait()
    except asyncio.CancelledError:
        logger.info("[SHUTDOWN] | Task: Web Server | Status: Terminating (SIGTERM)...")
        process.terminate()
        await process.wait()
        logger.info("[SHUTDOWN] | Task: Web Server | Status: Clean Shutdown")

    if process.returncode != 0 and process.returncode != -15:
        logger.error("[RUNTIME] | Task: Web Server | Status: CRASHED | ExitCode: %s", process.returncode)
        raise RuntimeError(f"Gunicorn failed with exit code {process.returncode}")


async def run_metax_app() -> None:
    init_logger()
    app = create_metax_django_app()
    logger.info("[SYSTEM] | Application bootstrap started")
    from metax.frameworks_and_drivers.di.metax_container import MetaxContainer, init_resources, shutdown_resources  # noqa: E402

    container: MetaxContainer = app.container  # type: ignore[attr-defined]

    try:
        await init_resources(container)
        opensearch_client = await container.opensearch_async_client.async_()
        await run_entrypoint(opensearch_client)
        await run_django_uvicorn_server()

    except asyncio.CancelledError, KeyboardInterrupt:
        logger.warning("[SHUTDOWN] | Stop signal received. Cleaning up...")
    except Exception as e:
        logger.critical("[RUNTIME] | Unhandled Exception during startup: %s", e, exc_info=True)
        sys.exit(1)
    finally:
        logger.info("[SHUTDOWN] | Releasing resources...")
        await shutdown_resources(container)
        logger.info("[SHUTDOWN] | Metax Shut downed!")


if __name__ == "__main__":
    try:
        asyncio.run(run_metax_app())
    except KeyboardInterrupt:
        pass
