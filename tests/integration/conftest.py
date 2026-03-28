from typing import AsyncIterator

import pytest
from opensearchpy import AsyncOpenSearch

from metax.frameworks_and_drivers.di.metax_container import (
    MetaxContainer,
    get_metax_container,
    init_resources,
    shutdown_resources,
)


@pytest.fixture(scope="session")
async def metax_container_for_integration_tests() -> AsyncIterator[MetaxContainer]:
    service_container_instance = get_metax_container()
    await init_resources(service_container_instance)
    yield service_container_instance
    await shutdown_resources(service_container_instance)


@pytest.fixture(scope="session", autouse=True)
async def setup_opensearch_migration(
    metax_container_for_integration_tests: MetaxContainer,
) -> AsyncIterator[None]:
    from metax.frameworks_and_drivers.opensearch.migration import migrate_indices, delete_all_indices

    opensearch_async_client_ = await metax_container_for_integration_tests.opensearch_async_client.async_()
    await migrate_indices(opensearch_async_client_)
    yield None
    await delete_all_indices(opensearch_async_client_)


async def refresh_opensearch_index(metax_container: MetaxContainer, index_or_alias_name: str) -> None:
    opensearch_async_client_ = await metax_container.opensearch_async_client.async_()
    response = await opensearch_async_client_.indices.refresh(index=index_or_alias_name)
    is_refreshed = int(response["_shards"]["successful"]) != 0
    assert is_refreshed


@pytest.fixture(autouse=True)
async def clear_os_each_test(metax_container_for_integration_tests: MetaxContainer) -> AsyncIterator[None]:
    client: AsyncOpenSearch = await metax_container_for_integration_tests.opensearch_async_client.async_()

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
