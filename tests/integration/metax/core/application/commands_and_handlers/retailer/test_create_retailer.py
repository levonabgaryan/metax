from uuid import uuid7

import pytest

from metax.core.application.commands_handlers.retailer import (
    CreateRetailerCommand,
    CreateRetailerCommandHandler,
)
from metax.core.domain.entities.retailer.value_objects import RetailersNames
from metax_application_manager import MetaxApplicationManager


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_create_retailer_command_handler(
    metax_app_for_integration_tests: MetaxApplicationManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_app_for_integration_tests.get_di_container()
    unit_of_work_provider = (
        metax_container_for_integration_tests.patterns_container.container.unit_of_work_provider()
    )
    event_bus = await metax_container_for_integration_tests.patterns_container.container.event_bus.async_()
    cmd = CreateRetailerCommand(
        retailer_uuid=uuid7(),
        name=RetailersNames.YEREVAN_CITY,
        url="https://example.com",
        phone_number="test_phone_number",
    )

    # when
    cmd_handler = CreateRetailerCommandHandler(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
    await cmd_handler.handle_command(cmd)

    # then
    uow = await unit_of_work_provider.create()
    async with uow:
        retailer = await uow.retailer_repo.get_by_uuid(cmd.retailer_uuid)

    assert retailer.get_name() == RetailersNames.YEREVAN_CITY
    assert retailer.get_home_page_url() == "https://example.com"
    assert retailer.get_phone_number() == "test_phone_number"
