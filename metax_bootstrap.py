from functools import lru_cache

from metax.frameworks_and_drivers.di.metax_container import MetaxContainer
from metax_configs import configuration_factory
from metax_lifespan import MetaxAppLifespanManager

METAX_CONFIGS = configuration_factory()
METAX_CONTAINER = MetaxContainer(metax_configs=METAX_CONFIGS)


@lru_cache(maxsize=1)
def get_metax_lifespan_manager() -> MetaxAppLifespanManager:
    return MetaxAppLifespanManager(metax_configs=METAX_CONFIGS, metax_container=METAX_CONTAINER)
