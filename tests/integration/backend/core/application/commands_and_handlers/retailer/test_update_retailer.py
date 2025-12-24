import pytest

from backend.core.application.commands_and_handlers.retailer import UpdateRetailerCommand
from backend.core.application.patterns.command_handler_abc import CommandHandler
from backend.core.application.ports.patterns.unit_of_work import UnitOfWork
from backend.frameworks_and_drivers.di.commands_handlers_container import RetailerCommandsHandlersContainer
from tests.integration.conftest import make_retailer_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_retailer_command_handler(
    unit_of_work: UnitOfWork, retailer_commands_handlers: RetailerCommandsHandlersContainer
) -> None:
    # given
    retailer = make_retailer_entity()

    cmd = UpdateRetailerCommand(
        retailer_uuid=retailer.get_uuid(),
        new_name="test_new_name",
        new_url="test_new_url",
        new_phone_number="test_new_phone_number",
    )

    async with unit_of_work as uow:
        await uow.repositories.retailer.add(retailer)
        await uow.commit()

    # when
    cmd_handler: CommandHandler[UpdateRetailerCommand] = retailer_commands_handlers.update_retailer(
        unit_of_work=unit_of_work
    )
    await cmd_handler.handle(cmd)

    # then
    async with unit_of_work as uow:
        updated_retailer = await uow.repositories.retailer.get_by_uuid(retailer.get_uuid())
        await uow.commit()

    assert updated_retailer.get_name() == "test_new_name"
    assert updated_retailer.get_url() == "test_new_url"
    assert updated_retailer.get_phone_number() == "test_new_phone_number"
