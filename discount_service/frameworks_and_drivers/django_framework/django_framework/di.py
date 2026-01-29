from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer

_service_container = None


def init_container() -> ServiceContainer:
    global _service_container

    if _service_container is None:
        from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer

        _service_container = ServiceContainer()

    return _service_container
