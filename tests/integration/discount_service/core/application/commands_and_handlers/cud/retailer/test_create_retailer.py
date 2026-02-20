from uuid import uuid4
import pytest

from discount_service.core.application.commands_and_handlers.cud.retailer import (
    CreateRetailerCommand,
)
from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_create_retailer_command_handler(
    service_container_for_tests: ServiceContainer,
) -> None:
    # given
    unit_of_work = await service_container_for_tests.patterns_container.container.unit_of_work.async_()
    cmd = CreateRetailerCommand(
        retailer_uuid=uuid4(),
        name="test_retailer",
        url="https://example.com",
        phone_number="test_phone_number",
    )

    # when
    cmd_handler = await service_container_for_tests.commands_handlers_container.container.retailer.container.create_retailer.async_()
    await cmd_handler.handle(cmd)

    # then
    async with unit_of_work as uow:
        retailer = await uow.retailer_repo.get_by_uuid(cmd.retailer_uuid)
        await uow.commit()

    assert retailer.get_name() == "test_retailer"
    assert retailer.get_home_page_url() == "https://example.com"
    assert retailer.get_phone_number() == "test_phone_number"
