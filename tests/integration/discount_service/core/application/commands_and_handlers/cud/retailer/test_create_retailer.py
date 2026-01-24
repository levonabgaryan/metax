from uuid import uuid4
import pytest
from dependency_injector.wiring import Provide, inject

from discount_service.core.application.commands_and_handlers.cud.retailer import (
    CreateRetailerCommand,
    CreateRetailerCommandHandler,
)
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.frameworks_and_drivers.di.boostrap import ServiceContainer


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@inject
async def test_create_retailer_command_handler(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
    command_handler: CreateRetailerCommandHandler = Provide[
        ServiceContainer.commands_handlers_container.container.retailer.container.create_retailer
    ],
) -> None:
    # given
    cmd = CreateRetailerCommand(
        retailer_uuid=uuid4(),
        name="test_retailer",
        url="https://example.com",
        phone_number="test_phone_number",
    )

    # when
    cmd_handler = command_handler
    await cmd_handler.handle(cmd)

    # then
    async with unit_of_work as uow:
        retailer = await uow.retailer_repo.get_by_uuid(cmd.retailer_uuid)
        await uow.commit()

    assert retailer.get_name() == "test_retailer"
    assert retailer.get_url() == "https://example.com"
    assert retailer.get_phone_number() == "test_phone_number"
