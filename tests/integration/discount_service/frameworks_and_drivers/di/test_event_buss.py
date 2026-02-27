import pytest

from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer


@pytest.mark.asyncio
async def test_message_buss_is_singleton(service_container_for_tests: ServiceContainer) -> None:
    event_bus_1 = await service_container_for_tests.patterns_container.container.event_bus.async_()
    event_bus_2 = await service_container_for_tests.patterns_container.container.event_bus.async_()
    event_bus_3 = await service_container_for_tests.patterns_container.container.event_bus.async_()

    assert event_bus_1 is event_bus_2 is event_bus_3


@pytest.mark.asyncio
async def test_message_buss_creates_different_uow_objects(service_container_for_tests: ServiceContainer) -> None:
    pass
