import pytest
from dependency_injector.wiring import Provide, inject

from discount_service.core.application.commands_and_handlers.cud.retailer import (
    UpdateRetailerCommand,
    UpdateRetailerCommandHandler,
)
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer
from tests.utils import make_retailer_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@inject
async def test_update_retailer_command_handler(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
    command_handler: UpdateRetailerCommandHandler = Provide[
        ServiceContainer.commands_handlers_container.container.retailer.container.update_retailer
    ],
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
        await uow.retailer_repo.add(retailer)
        await uow.commit()

    # when
    cmd_handler = command_handler
    await cmd_handler.handle(cmd)

    # then
    async with unit_of_work as uow:
        updated_retailer = await uow.retailer_repo.get_by_uuid(retailer.get_uuid())
        await uow.commit()

    assert updated_retailer.get_name() == "test_new_name"
    assert updated_retailer.get_home_page_url() == "test_new_url"
    assert updated_retailer.get_phone_number() == "test_new_phone_number"
