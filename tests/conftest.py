"""Shared pytest hooks for all tests under ``tests/``."""

from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

import pytest
from asgiref.sync import sync_to_async

from metax_bootstrap import METAX_LIFESPAN_MANAGER
from metax_lifespan import MetaxAppLifespanManager
from tests.db_teardown import close_django_db_connections_and_pools

if TYPE_CHECKING:
    from dmr.test import DMRAsyncClient


@pytest.fixture
def dmr_async_client() -> DMRAsyncClient:
    from dmr.test import DMRAsyncClient

    return DMRAsyncClient()


@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:  # noqa: ARG001
    """Run before pytest default ``pytest_sessionfinish`` (which calls ``teardown_exact``).

    That teardown destroys session fixtures including pytest-django
    ``django_db_setup`` then ``teardown_databases``. Closing pools here avoids Postgres
    sessions still attached during ``DROP DATABASE``.
    """
    with contextlib.suppress(Exception):
        close_django_db_connections_and_pools()


@pytest.fixture(scope="session")
async def metax_lifespan_manager_for_tests(
    django_db_setup: None,  # noqa: ARG001
) -> AsyncIterator[MetaxAppLifespanManager]:
    metax_application_manager = METAX_LIFESPAN_MANAGER
    await metax_application_manager.init_metax_container_resources()
    metax_application_manager.configure_logger()
    metax_application_manager.configure_django_app()
    await metax_application_manager.run_databases_migrations()
    try:
        yield metax_application_manager
    finally:
        await metax_application_manager.shutdown_metax_container_resources()
        await sync_to_async(close_django_db_connections_and_pools, thread_sensitive=True)()
