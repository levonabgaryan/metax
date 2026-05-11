from metax.frameworks_and_drivers.di.metax_container import MetaxContainer
from metax_configs import configuration_factory
from metax_lifespan import MetaxAppLifespanManager

METAX_CONFIGS = configuration_factory()
METAX_CONTAINER = MetaxContainer(metax_configs=METAX_CONFIGS)
METAX_LIFESPAN_MANAGER = MetaxAppLifespanManager(metax_configs=METAX_CONFIGS, metax_container=METAX_CONTAINER)
