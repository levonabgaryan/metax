import contextlib
from typing import AsyncIterator

import pytest
from opensearchpy import AsyncOpenSearch

from metax_application_manager import METAX_APPLICATION_MANAGER, MetaxApplicationManager


@pytest.fixture(scope="session")
async def metax_app_for_integration_tests() -> AsyncIterator[MetaxApplicationManager]:
    await METAX_APPLICATION_MANAGER.init_di_container_resources()
    await METAX_APPLICATION_MANAGER.configure_logger()
    await METAX_APPLICATION_MANAGER.run_entrypoints()
    try:
        yield METAX_APPLICATION_MANAGER
    finally:
        await METAX_APPLICATION_MANAGER.shutdown_di_container_resources()


@pytest.fixture(scope="session", autouse=True)
async def setup_opensearch_migration(
    metax_app_for_integration_tests: MetaxApplicationManager,
) -> AsyncIterator[None]:
    from metax.frameworks_and_drivers.opensearch.migration import delete_all_indices, migrate_indices

    di_container = metax_app_for_integration_tests.get_di_container()
    opensearch_async_client_ = await di_container.opensearch_async_client.async_()
    await migrate_indices(opensearch_async_client_)
    yield None
    await delete_all_indices(opensearch_async_client_)


async def refresh_opensearch_index(
    metax_app_for_integration_tests: MetaxApplicationManager,
    index_or_alias_name: str,
) -> None:
    metax_container = metax_app_for_integration_tests.get_di_container()
    opensearch_async_client_ = await metax_container.opensearch_async_client.async_()
    response = await opensearch_async_client_.indices.refresh(index=index_or_alias_name)
    is_refreshed = int(response["_shards"]["successful"]) != 0
    assert is_refreshed


@pytest.fixture(autouse=True)
async def clear_os_each_test(
    metax_app_for_integration_tests: MetaxApplicationManager,
) -> AsyncIterator[None]:
    di_container = metax_app_for_integration_tests.get_di_container()
    client: AsyncOpenSearch = await di_container.opensearch_async_client.async_()

    async def cleanup() -> None:
        with contextlib.suppress(Exception):
            await client.delete_by_query(
                index="*,-.*",
                body={"query": {"match_all": {}}},
                refresh=True,
                ignore_unavailable=True,
                wait_for_completion=True,
            )

    await cleanup()
    yield
    await cleanup()
