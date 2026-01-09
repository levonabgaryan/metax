from discount_service.frameworks_and_drivers.di.boostrap import ServiceContainer


def test_message_buss_is_singleton(service_container: ServiceContainer) -> None:
    msb_1 = service_container.patterns_container.container.message_bus()
    msb_2 = service_container.patterns_container.container.message_bus()
    msb_3 = service_container.patterns_container.container.message_bus()

    assert msb_1 is msb_2 is msb_3


def test_message_buss_creates_different_uow_objects(service_container: ServiceContainer) -> None:
    msb = service_container.patterns_container.container.message_bus()
    uow_1 = msb.create_unit_of_work()
    uow_2 = msb.create_unit_of_work()
    uow_3 = msb.create_unit_of_work()

    assert not all([uow_1 is uow_2 is uow_3])
