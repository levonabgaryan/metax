import pytest

from metax.frameworks_and_drivers.di.metax_container import MetaxContainer


@pytest.mark.asyncio
async def test_message_buss_is_singleton(metax_container_for_integration_tests: MetaxContainer) -> None:
    event_bus_1 = metax_container_for_integration_tests.patterns_container.container.event_bus()
    event_bus_2 = metax_container_for_integration_tests.patterns_container.container.event_bus()
    event_bus_3 = metax_container_for_integration_tests.patterns_container.container.event_bus()

    assert event_bus_1 is event_bus_2 is event_bus_3
