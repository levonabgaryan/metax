import pytest

from metax.frameworks_and_drivers.di.bootstrap import MetaxContainer


@pytest.mark.asyncio
async def test_message_buss_is_singleton(service_container_for_integration_tests: MetaxContainer) -> None:
    event_bus_1 = service_container_for_integration_tests.patterns_container.container.event_bus()
    event_bus_2 = service_container_for_integration_tests.patterns_container.container.event_bus()
    event_bus_3 = service_container_for_integration_tests.patterns_container.container.event_bus()

    assert event_bus_1 is event_bus_2 is event_bus_3
