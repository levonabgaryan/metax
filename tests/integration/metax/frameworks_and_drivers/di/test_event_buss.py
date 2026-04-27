import pytest

from metax_lifespan import MetaxAppLifespanManager


@pytest.mark.asyncio
async def test_message_buss_is_singleton(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    metax_container_for_integration_tests = metax_lifespan_manager_for_integration_tests.get_di_container()
    event_bus_1 = await metax_container_for_integration_tests.resources_container.container.event_bus.async_()
    event_bus_2 = await metax_container_for_integration_tests.resources_container.container.event_bus.async_()
    event_bus_3 = await metax_container_for_integration_tests.resources_container.container.event_bus.async_()

    assert event_bus_1 is event_bus_2 is event_bus_3
