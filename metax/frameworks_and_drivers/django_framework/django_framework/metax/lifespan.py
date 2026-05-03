from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from django_asgi_lifespan.types import State

from metax_bootstrap import get_metax_lifespan_manager


@asynccontextmanager
async def app_lifespan_manager() -> AsyncIterator[State]:
    manager = get_metax_lifespan_manager()

    metax_lifespan_manager = get_metax_lifespan_manager()
    await metax_lifespan_manager.init_metax_container_resources()
    metax_lifespan_manager.configure_logger()
    metax_lifespan_manager.configure_django_app()
    await metax_lifespan_manager.run_entrypoints()

    state: State = {}

    try:
        yield state
    finally:
        await manager.shutdown_metax_container_resources()
