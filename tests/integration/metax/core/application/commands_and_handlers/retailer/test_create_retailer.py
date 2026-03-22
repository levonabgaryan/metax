from uuid import uuid4
import pytest

from metax.core.application.commands_handlers.retailer import (
    CreateRetailerCommand,
    CreateRetailerCommandHandler,
)
from metax.frameworks_and_drivers.di.bootstrap import ServiceContainer


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_create_retailer_command_handler(
    service_container_for_integration_tests: ServiceContainer,
) -> None:
    # given
    unit_of_work = await service_container_for_integration_tests.patterns_container.container.unit_of_work.async_()
    event_bus = await service_container_for_integration_tests.patterns_container.container.event_bus.async_()
    cmd = CreateRetailerCommand(
        retailer_uuid=uuid4(),
        name="yerevan-city",
        url="https://example.com",
        phone_number="test_phone_number",
    )

    # when
    cmd_handler = CreateRetailerCommandHandler(unit_of_work=unit_of_work, event_bus=event_bus)
    await cmd_handler.handle_command(cmd)

    # then
    retailer = await unit_of_work.retailer_repo.get_by_uuid(cmd.retailer_uuid)

    assert retailer.get_name().value == "yerevan-city"
    assert retailer.get_home_page_url() == "https://example.com"
    assert retailer.get_phone_number() == "test_phone_number"
