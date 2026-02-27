import pytest

from discount_service.core.application.commands_handlers.retailer import (
    UpdateRetailerCommand,
    UpdateRetailerCommandHandler,
)
from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer
from tests.utils import make_retailer_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_retailer_command_handler(
    service_container_for_tests: ServiceContainer,
) -> None:
    # given
    unit_of_work = await service_container_for_tests.patterns_container.container.unit_of_work.async_()
    event_bus = await service_container_for_tests.patterns_container.container.event_bus.async_()

    retailer = make_retailer_entity()

    cmd = UpdateRetailerCommand(
        retailer_uuid=retailer.get_uuid(),
        new_name="test_new_name",
        new_url="test_new_url",
        new_phone_number="test_new_phone_number",
    )

    async with unit_of_work as uow:
        await uow.retailer_repo.add(retailer)
        await uow.commit()

    # when
    cmd_handler = UpdateRetailerCommandHandler(unit_of_work=unit_of_work, event_bus=event_bus)
    await cmd_handler.handle_command(cmd)

    # then
    async with unit_of_work as uow:
        updated_retailer = await uow.retailer_repo.get_by_uuid(retailer.get_uuid())
        await uow.commit()

    assert updated_retailer.get_name() == "test_new_name"
    assert updated_retailer.get_home_page_url() == "test_new_url"
    assert updated_retailer.get_phone_number() == "test_new_phone_number"
