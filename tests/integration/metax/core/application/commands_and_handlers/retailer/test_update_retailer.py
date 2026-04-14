import pytest

from metax.core.application.commands_handlers.retailer import (
    UpdateRetailerCommand,
    UpdateRetailerCommandHandler,
)
from metax.core.domain.entities.retailer.value_objects import RetailersNames
from metax_application_manager import MetaxApplicationManager
from tests.utils import make_retailer_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_retailer_command_handler(
    metax_app_for_integration_tests: MetaxApplicationManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_app_for_integration_tests.get_di_container()
    unit_of_work_provider = (
        metax_container_for_integration_tests.patterns_container.container.unit_of_work_provider()
    )
    event_bus = await metax_container_for_integration_tests.patterns_container.container.event_bus.async_()
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()

    retailer = make_retailer_entity()

    cmd = UpdateRetailerCommand(
        retailer_uuid=retailer.get_uuid(),
        new_name=RetailersNames.SAS_AM.value,
        new_url="test_new_url",
        new_phone_number="test_new_phone_number",
    )

    async with unit_of_work as uow:
        await uow.retailer_repo.add(retailer)
        await uow.commit()

    # when
    cmd_handler = UpdateRetailerCommandHandler(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
    await cmd_handler.handle_command(cmd)

    # then
    uow = await unit_of_work_provider.create()
    async with uow:
        updated_retailer = await uow.retailer_repo.get_by_uuid(retailer.get_uuid())
        await uow.commit()

    assert updated_retailer.get_name() == RetailersNames.SAS_AM
    assert updated_retailer.get_home_page_url() == "test_new_url"
    assert updated_retailer.get_phone_number() == "test_new_phone_number"
