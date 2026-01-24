import pytest
from dependency_injector.wiring import Provide, inject

from discount_service.core.application.commands_and_handlers.cud.category import (
    UpdateCategoryCommand,
    UpdateCategoryCommandHandler,
)
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.frameworks_and_drivers.di.boostrap import ServiceContainer

from tests.utils import make_category_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@inject
async def test_update_category_command_handler(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
    command_handler: UpdateCategoryCommandHandler = Provide[
        ServiceContainer.commands_handlers_container.container.category.container.update_category
    ],
) -> None:
    # given
    category = make_category_entity()

    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    # when
    cmd = UpdateCategoryCommand(category_uuid=category.get_uuid(), new_name="new_test_name")
    cmd_handler = command_handler
    await cmd_handler.handle(cmd)

    # then
    assert cmd.fields_to_update.name is True
    async with unit_of_work as uow:
        updated_category = await uow.category_repo.get_by_uuid(category.get_uuid())
        assert updated_category.get_name() == cmd.new_name
        await uow.commit()
