from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

from filelock import AsyncFileLock
from opensearchpy import AsyncOpenSearch

from metax_configs import BaseConfigs

logger = logging.getLogger(__name__)

lock = AsyncFileLock("/tmp/migrations.lock", timeout=0)  # noqa: S108


async def _run_postgres_db_migrations(metax_configs: BaseConfigs) -> None:

    manage_py = Path(metax_configs.django_dir) / "manage.py"
    logger.info("STARTUP | Task: Postgres Migrations | Status: Started")

    for command in ["makemigrations", "migrate"]:
        process = await asyncio.create_subprocess_exec(
            sys.executable, str(manage_py), command, cwd=metax_configs.django_dir
        )
        await process.wait()
        if process.returncode != 0:
            logger.error("STARTUP | Task: Postgres Migrations | Status: FAILED | Step: %s", command)
            msg = f"Django {command} failed with exit code {process.returncode}"
            raise RuntimeError(msg)

    logger.info("STARTUP | Task: Postgres Migrations | Status: SUCCESS")


async def _run_opensearch_db_migrations(client: AsyncOpenSearch) -> None:
    from metax.frameworks_and_drivers.opensearch.migration import migrate_indices

    logger.info("STARTUP | Task: OpenSearch Migrations | Status: Started")
    try:
        await migrate_indices(client=client)
        logger.info("STARTUP | Task: OpenSearch Migrations | Status: SUCCESS")
    except Exception as e:
        logger.error("STARTUP | Task: OpenSearch Migrations | Status: FAILED | Error: %s", e)
        raise


async def run_databases_migrations(metax_configs: BaseConfigs, client: AsyncOpenSearch) -> None:
    try:
        async with lock:  # Since Gunicorn can run multiple uvicorn workers, one of them should run migrations
            logger.info("STARTUP | Task: RUN DATABASES MIGRATIONS | Status: Started")
            await _run_opensearch_db_migrations(client=client)
            await _run_postgres_db_migrations(metax_configs=metax_configs)
            logger.info("STARTUP | Task: RUN DATABASES MIGRATIONS | Status: SUCCESS")
    except (TimeoutError, Exception) as err:
        if "Timeout" in str(err) or isinstance(err, asyncio.TimeoutError):
            logger.info("STARTUP | Migrations are already running in another process. Skipping.")
        else:
            logger.error("STARTUP | Migrations failed: %s", err)
            raise
