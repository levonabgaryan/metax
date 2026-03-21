import logging
import os
import sys
import asyncio
from pathlib import Path

from django.apps import AppConfig
from opensearchpy import AsyncOpenSearch

from config_ import metax_configs

PROJECT_ROOT = metax_configs.project_root_pythonpath
DJANGO_PATH = metax_configs.django_dir

sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, DJANGO_PATH)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_framework.settings")  # noqa: E402

logger = logging.getLogger(__name__)


# -------------------------
# Django
# -------------------------


async def run_postgres_db_migrations() -> None:
    manage_py = Path(metax_configs.django_dir) / "manage.py"
    logger.info("[STARTUP] | Task: Postgres Migrations | Status: Started")

    for command in ["makemigrations", "migrate"]:
        process = await asyncio.create_subprocess_exec(
            sys.executable, str(manage_py), command, cwd=metax_configs.django_dir
        )
        await process.wait()
        if process.returncode != 0:
            logger.error("[STARTUP] | Task: Postgres Migrations | Status: FAILED | Command: %s", command)
            raise RuntimeError(f"Django {command} failed with exit code {process.returncode}")

    logger.info("[STARTUP] | Task: Postgres Migrations | Status: SUCCESS")


# -------------------------
# OpenSearch (Native Async)
# -------------------------


async def run_opensearch_db_migrations(client: AsyncOpenSearch) -> None:
    from metax.frameworks_and_drivers.opensearch.migration import migrate_indices  # noqa: E402

    logger.info("[STARTUP] | Task: OpenSearch Migrations | Status: Started")
    try:
        await migrate_indices(client=client)
        logger.info("[STARTUP] | Task: OpenSearch Migrations | Status: SUCCESS")
    except Exception as e:
        logger.error("[STARTUP] | Task: OpenSearch Migrations | Status: FAILED | Error: %s", e)
        raise


# -------------------------
# Server (Async Subprocess)
# -------------------------


async def run_django_uvicorn_server() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(PROJECT_ROOT), str(DJANGO_PATH)])
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
            str(PROJECT_ROOT),
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


def create_app() -> AppConfig:
    from django.apps import apps
    from metax.frameworks_and_drivers.di.bootstrap import configured_service_container  # noqa: E402

    container = configured_service_container()
    metax_app = apps.get_app_config("metax")
    metax_app.container = container  # type: ignore[attr-defined]
    return metax_app


# -------------------------
# Entry point
# -------------------------


async def run_metax_app() -> None:
    import django

    logger.info("[SYSTEM] | Application bootstrap started")

    django.setup()
    from metax.frameworks_and_drivers.di import ServiceContainer  # noqa: E402

    app = create_app()
    container: ServiceContainer = app.container  # type: ignore[attr-defined]
    opensearch_client = await container.opensearch_async_client.async_()

    try:
        init_task = container.init_resources()
        if init_task:
            await init_task

        await run_postgres_db_migrations()
        await run_opensearch_db_migrations(client=opensearch_client)
        await run_django_uvicorn_server()

    except asyncio.CancelledError, KeyboardInterrupt:
        logger.warning("[SHUTDOWN] | Stop signal received. Cleaning up...")
    except Exception as e:
        logger.critical("[RUNTIME] | Unhandled Exception during startup: %s", e, exc_info=True)
        sys.exit(1)
    finally:
        logger.info("[SHUTDOWN] | Releasing resources...")
        shutdown_task = container.shutdown_resources()
        if shutdown_task:
            await shutdown_task
        logger.info("[SHUTDOWN] | Metax Shut downed!")


if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(run_metax_app())
    except KeyboardInterrupt:
        pass
