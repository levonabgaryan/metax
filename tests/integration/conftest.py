from typing import AsyncIterator

import pytest
from pytest_django.plugin import DjangoDbBlocker
from dependency_injector.wiring import inject, Provide
from opensearchpy import AsyncOpenSearch

from config import discount_service_configs
from discount_service.frameworks_and_drivers.di import get_service_container
from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer


@pytest.fixture(scope="session", autouse=True)
async def service_container(django_db_blocker: DjangoDbBlocker) -> AsyncIterator[ServiceContainer]:
    service_container_instance = get_service_container()
    # with django_db_blocker.unblock():
    init_task = service_container_instance.init_resources()
    if init_task:
        await init_task

    service_container_instance.wire(
        packages=[__name__, "tests.integration"],
        warn_unresolved=True,
        modules=["discount_service.frameworks_and_drivers.celery_framework.tasks"],
    )
    yield service_container_instance

    shutdown_task = service_container_instance.shutdown_resources()
    if shutdown_task:
        await shutdown_task

    service_container_instance.unwire()


@inject
def get_current_container_for_tests(
    service_container: ServiceContainer = Provide[ServiceContainer],
) -> ServiceContainer:
    return service_container


@pytest.fixture(scope="session", autouse=True)
@inject
async def setup_opensearch_migration(
    opensearch_async_client_: AsyncOpenSearch = Provide[ServiceContainer.opensearch_async_client],
) -> AsyncIterator[None]:
    from discount_service.frameworks_and_drivers.opensearch.migration import migrate_indices, delete_all_indices

    await migrate_indices(opensearch_async_client_)
    yield None
    await delete_all_indices(opensearch_async_client_)


@pytest.fixture(scope="session")
def celery_config() -> dict[str, str]:
    return {
        "broker_url": f"{discount_service_configs.celery_broker_url}",
        "result_backend": f"{discount_service_configs.celery_result_backend_url}",
    }
