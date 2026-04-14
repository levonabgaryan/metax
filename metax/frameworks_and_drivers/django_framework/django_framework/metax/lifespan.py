from contextlib import asynccontextmanager
from typing import AsyncIterator

from django_asgi_lifespan.types import State

from metax_bootstrap import get_metax_lifespan_manager


@asynccontextmanager
async def app_lifespan_manager() -> AsyncIterator[State]:
    manager = get_metax_lifespan_manager()

    metax_application_manager = get_metax_lifespan_manager()
    await metax_application_manager.init_di_container_resources()
    await metax_application_manager.configure_logger()
    metax_application_manager.configure_django_app()
    await metax_application_manager.run_entrypoints()

    state: State = {}

    try:
        yield state
    finally:
        await manager.shutdown_di_container_resources()
