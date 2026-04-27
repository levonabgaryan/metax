from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from opensearchpy import AsyncOpenSearch

from metax.core.application.event_handlers.event_bus import EventBus
from metax.core.application.ports.backend_patterns.provider.unit_of_work_provider import IUnitOfWorkProvider
from metax.core.application.ports.ddd_patterns.repository.read_models_repositories.discounted_product_read_model import (  # noqa: E501
    IDiscountedProductReadModelRepository,
)


@asynccontextmanager
async def async_opensearch_client_resource(
    host: str, port: int, user: str, password: str, verify_certs: bool
) -> AsyncIterator[AsyncOpenSearch]:
    # https://python-dependency-injector.ets-labs.org/providers/resource.html#:~:text=Asynchronous%20Context%20Manager%20initializer%3A
    client = AsyncOpenSearch(
        hosts=[{"host": host, "port": port}],
        http_auth=(user, password),
        use_ssl=True,
        verify_certs=verify_certs,
    )
    try:
        yield client
    finally:
        await client.close()


@asynccontextmanager
async def event_bus_resource(
    unit_of_work_provider: IUnitOfWorkProvider,
    discounted_product_read_model_repo: IDiscountedProductReadModelRepository,
) -> AsyncIterator[EventBus]:
    event_bus = EventBus(
        unit_of_work_provider=unit_of_work_provider,
        discounted_product_read_model_repo=discounted_product_read_model_repo,
    )
    try:
        event_bus.register()
        yield event_bus
    finally:
        await event_bus.shutdown()
