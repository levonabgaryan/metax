from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from metax.core.application.event_handlers.event_bus import EventBus
from metax.core.application.ports.backend_patterns.provider.unit_of_work_provider import IUnitOfWorkProvider


@asynccontextmanager
async def event_bus_resource(
    unit_of_work_provider: IUnitOfWorkProvider,
) -> AsyncIterator[EventBus]:
    event_bus = EventBus(
        unit_of_work_provider=unit_of_work_provider,
    )
    try:
        event_bus.register()
        yield event_bus
    finally:
        await event_bus.shutdown()
