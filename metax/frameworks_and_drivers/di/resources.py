from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from metax.core.application.event_handlers.event_bus import EventBus
from metax.core.application.ports.backend_patterns.provider.unit_of_work_provider import IUnitOfWorkProvider
from metax.core.application.ports.ddd_patterns.repository.read_models_repositories.discounted_product_read_model import (  # noqa: E501
    DiscountedProductReadModelRepository,
)


@asynccontextmanager
async def event_bus_resource(
    unit_of_work_provider: IUnitOfWorkProvider,
    discounted_product_read_model_repo: DiscountedProductReadModelRepository,
    embed_after_collect: bool = True,
) -> AsyncIterator[EventBus]:
    event_bus = EventBus(
        unit_of_work_provider=unit_of_work_provider,
        discounted_product_read_model_repo=discounted_product_read_model_repo,
        embed_after_collect=embed_after_collect,
    )
    try:
        event_bus.register()
        yield event_bus
    finally:
        await event_bus.shutdown()
