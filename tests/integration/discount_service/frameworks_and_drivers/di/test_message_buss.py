import pytest

from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer


def test_message_buss_is_singleton(service_container_for_tests: ServiceContainer) -> None:
    msb_1 = service_container_for_tests.patterns_container.container.message_bus()
    msb_2 = service_container_for_tests.patterns_container.container.message_bus()
    msb_3 = service_container_for_tests.patterns_container.container.message_bus()

    assert msb_1 is msb_2 is msb_3


@pytest.mark.asyncio
async def test_message_buss_creates_different_uow_objects(service_container_for_tests: ServiceContainer) -> None:
    msb = service_container_for_tests.patterns_container.container.message_bus()
    uow_1 = await msb.create_unit_of_work()
    uow_2 = await msb.create_unit_of_work()
    uow_3 = await msb.create_unit_of_work()

    assert not all([uow_1 is uow_2 is uow_3])
