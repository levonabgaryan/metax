from typing import AsyncIterator

import pytest
from asgiref.sync import sync_to_async
from dependency_injector.wiring import inject, Provide
from django.db import connections
from opensearchpy import AsyncOpenSearch
from pytest_django import DjangoDbBlocker

from discount_service.frameworks_and_drivers.di import get_service_container
from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer


@pytest.fixture(scope="session")
async def service_container_for_integration_tests(
    django_db_blocker: DjangoDbBlocker,
) -> AsyncIterator[ServiceContainer]:
    service_container_instance = get_service_container()
    init_task = service_container_instance.init_resources()
    if init_task:
        await init_task

    service_container_instance.wire(
        packages=[__name__, "tests.integration", "tests.e2e"],
        warn_unresolved=True,
        modules=["discount_service.frameworks_and_drivers.celery_framework.tasks"],
    )
    yield service_container_instance
    import asyncio

    await asyncio.sleep(0.1)

    with django_db_blocker.unblock():

        def close_django_connections() -> None:
            for conn in connections.all():
                conn.close_if_unusable_or_obsolete()
                conn.close()

        await sync_to_async(close_django_connections)()

    shutdown_task = service_container_instance.shutdown_resources()
    if shutdown_task:
        await shutdown_task

    service_container_instance.unwire()


@pytest.fixture(scope="session", autouse=True)
async def setup_opensearch_migration(
    service_container_for_integration_tests: ServiceContainer,
) -> AsyncIterator[None]:
    from discount_service.frameworks_and_drivers.opensearch.migration import migrate_indices, delete_all_indices

    opensearch_async_client_ = await service_container_for_integration_tests.opensearch_async_client.async_()
    await migrate_indices(opensearch_async_client_)
    yield None
    await delete_all_indices(opensearch_async_client_)


@inject
async def refresh_opensearch_index(
    index_or_alias_name: str,
    opensearch_async_client_: AsyncOpenSearch = Provide[ServiceContainer.opensearch_async_client],
) -> None:
    response = await opensearch_async_client_.indices.refresh(index=index_or_alias_name)
    is_refreshed = int(response["_shards"]["successful"]) != 0
    assert is_refreshed


@inject
def get_current_container_for_tests(
    service_container: ServiceContainer = Provide[ServiceContainer],
) -> ServiceContainer:
    return service_container


def pytest_configure(config: pytest.Config) -> None:
    from django.db.backends.postgresql.creation import DatabaseCreation
    from typing import Any

    original_destroy_test_db = DatabaseCreation._destroy_test_db  # type: ignore

    def patched_destroy_test_db(self: DatabaseCreation, test_database_name: str, verbosity: Any) -> Any:
        with self.connection._nodb_cursor() as cursor:
            cursor.execute(f"""
                SELECT pid, application_name, state, query 
                FROM pg_stat_activity 
                WHERE datname = '{test_database_name}' AND pid <> pg_backend_pid();
            """)
            active_sessions = cursor.fetchall()
            if active_sessions:
                print(f"\n[DETECTED]: Found {len(active_sessions)} open sessions!")
                for s in active_sessions:
                    print(f"PID: {s[0]} | App: {s[1]} | State: {s[2]} | Last SQL: {s[3]}")

        with self.connection._nodb_cursor() as cursor:
            cursor.execute(f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{test_database_name}'
                  AND pid <> pg_backend_pid();
            """)
        return original_destroy_test_db(self, test_database_name, verbosity)

    DatabaseCreation._destroy_test_db = patched_destroy_test_db  # type: ignore


@pytest.fixture(autouse=True)
async def clear_os_each_test(service_container_for_integration_tests: ServiceContainer) -> AsyncIterator[None]:
    client: AsyncOpenSearch = await service_container_for_integration_tests.opensearch_async_client.async_()

    async def cleanup() -> None:
        try:
            await client.delete_by_query(
                index="*,-.*",
                body={"query": {"match_all": {}}},
                refresh=True,
                ignore_unavailable=True,
                wait_for_completion=True,
            )
        except Exception:
            pass

    await cleanup()
    yield
    await cleanup()
