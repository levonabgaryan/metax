from functools import lru_cache

from metax.frameworks_and_drivers.di.metax_container import MetaxContainer
from metax_configs import METAX_CONFIGS
from metax_lifespan import MetaxAppLifespanManager


@lru_cache(maxsize=1)
def get_metax_lifespan_manager() -> MetaxAppLifespanManager:
    return MetaxAppLifespanManager(metax_configs=METAX_CONFIGS, metax_di_container=MetaxContainer())
