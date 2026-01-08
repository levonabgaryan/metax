from uuid import uuid4
import pytest

from discount_service.core.application.commands_and_handlers.cud.retailer import CreateRetailerCommand
from discount_service.core.application.patterns.command_handler_abc import CommandHandler
from discount_service.core.application.ports.patterns.unit_of_work import UnitOfWork
from discount_service.frameworks_and_drivers.di.commands_handlers_container import (
    RetailerCommandsHandlersContainer,
)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_create_retailer_command_handler(
    unit_of_work: UnitOfWork, retailer_commands_handlers: RetailerCommandsHandlersContainer
) -> None:
    # given
    cmd = CreateRetailerCommand(
        retailer_uuid=uuid4(),
        name="test_retailer",
        url="https://example.com",
        phone_number="test_phone_number",
    )

    # when
    cmd_handler: CommandHandler[CreateRetailerCommand] = retailer_commands_handlers.create_retailer(
        unit_of_work=unit_of_work,
    )
    await cmd_handler.handle(cmd)

    # then
    async with unit_of_work as uow:
        retailer = await uow.repositories.retailer.get_by_uuid(cmd.retailer_uuid)
        await uow.commit()

    assert retailer.get_name() == "test_retailer"
    assert retailer.get_url() == "https://example.com"
    assert retailer.get_phone_number() == "test_phone_number"
