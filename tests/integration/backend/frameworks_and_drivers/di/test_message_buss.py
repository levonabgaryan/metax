from backend.frameworks_and_drivers.di.boostrap import MainContainer


def test_message_buss_is_singleton(container: MainContainer) -> None:
    msb_1 = container.patterns.container.message_bus()
    msb_2 = container.patterns.container.message_bus()
    msb_3 = container.patterns.container.message_bus()

    assert msb_1 is msb_2 is msb_3


def test_message_buss_creates_different_uow_objects(container: MainContainer) -> None:
    msb = container.patterns.container.message_bus()
    uow_1 = msb.create_unit_of_work()
    uow_2 = msb.create_unit_of_work()
    uow_3 = msb.create_unit_of_work()

    assert not all([uow_1 is uow_2 is uow_3])


def test_message_buss_is_singleton_in_controllers(container: MainContainer) -> None:
    category_controller_1 = container.controllers().category_controller()
    category_controller_2 = container.controllers().category_controller()

    assert category_controller_1.message_bus is category_controller_2.message_bus
