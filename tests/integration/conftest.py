from typing import AsyncIterator

import pytest
from dependency_injector.wiring import inject, Provide
from opensearchpy import AsyncOpenSearch

from metax.frameworks_and_drivers.di import get_metax_container
from metax.frameworks_and_drivers.di.bootstrap import MetaxContainer


@pytest.fixture(scope="session")
async def service_container_for_integration_tests() -> AsyncIterator[MetaxContainer]:
    service_container_instance = get_metax_container()
    init_task = service_container_instance.init_resources()
    if init_task:
        await init_task

    service_container_instance.wire(
        packages=[__name__, "tests.integration", "tests.e2e"],
        warn_unresolved=True,
        modules=["metax.frameworks_and_drivers.celery_framework.tasks"],
    )
    yield service_container_instance

    shutdown_task = service_container_instance.shutdown_resources()
    if shutdown_task:
        await shutdown_task

    service_container_instance.unwire()


@pytest.fixture(scope="session", autouse=True)
async def setup_opensearch_migration(
    service_container_for_integration_tests: MetaxContainer,
) -> AsyncIterator[None]:
    from metax.frameworks_and_drivers.opensearch.migration import migrate_indices, delete_all_indices

    opensearch_async_client_ = await service_container_for_integration_tests.opensearch_async_client.async_()
    await migrate_indices(opensearch_async_client_)
    yield None
    await delete_all_indices(opensearch_async_client_)


@inject
async def refresh_opensearch_index(
    index_or_alias_name: str,
    opensearch_async_client_: AsyncOpenSearch = Provide[MetaxContainer.opensearch_async_client],
) -> None:
    response = await opensearch_async_client_.indices.refresh(index=index_or_alias_name)
    is_refreshed = int(response["_shards"]["successful"]) != 0
    assert is_refreshed


@inject
def get_current_container_for_tests(
    service_container: MetaxContainer = Provide[MetaxContainer],
) -> MetaxContainer:
    return service_container


@pytest.fixture(autouse=True)
async def clear_os_each_test(service_container_for_integration_tests: MetaxContainer) -> AsyncIterator[None]:
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
