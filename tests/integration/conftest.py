from typing import AsyncIterator

import pytest
from dependency_injector.wiring import inject, Provide
from opensearchpy import AsyncOpenSearch

from discount_service.frameworks_and_drivers.di import get_service_container
from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer


@pytest.fixture(scope="session")
async def service_container_for_integration_tests() -> AsyncIterator[ServiceContainer]:
    service_container_instance = get_service_container()
    # with django_db_blocker.unblock():
    init_task = service_container_instance.init_resources()
    if init_task:
        await init_task

    service_container_instance.wire(
        packages=[__name__, "tests.integration", "tests.e2e"],
        warn_unresolved=True,
        modules=["discount_service.frameworks_and_drivers.celery_framework.tasks"],
    )
    yield service_container_instance

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
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{test_database_name}'
                  AND pid <> pg_backend_pid();
            """)
        return original_destroy_test_db(self, test_database_name, verbosity)

    DatabaseCreation._destroy_test_db = patched_destroy_test_db  # type: ignore
