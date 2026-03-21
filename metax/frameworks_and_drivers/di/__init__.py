from metax.frameworks_and_drivers.di.bootstrap import ServiceContainer

_service_container = None


def get_service_container() -> ServiceContainer:
    global _service_container

    if _service_container is None:
        from metax.frameworks_and_drivers.di.bootstrap import configured_service_container

        _service_container = configured_service_container()

    return _service_container


__all__ = ("ServiceContainer", "get_service_container")
