import pytest

from backend.core.application.commands_and_handlers.category import (
    UpdateCategoryCommand,
)
from backend.core.application.patterns.command_handler_abc import CommandHandler
from backend.core.application.ports.patterns.unit_of_work import UnitOfWork
from backend.frameworks_and_drivers.di.commands_handlers_container import CategoryCommandsHandlersContainer
from tests.integration.conftest import make_category_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_category_command_handler(
    unit_of_work: UnitOfWork, category_commands_handlers: CategoryCommandsHandlersContainer
) -> None:
    # given
    category = make_category_entity()

    async with unit_of_work as uow:
        await uow.repositories.category.add(category)
        await uow.commit()

    # when
    cmd = UpdateCategoryCommand(category_uuid=category.get_uuid(), new_name="new_test_name")
    cmd_handler: CommandHandler[UpdateCategoryCommand] = category_commands_handlers.update_category(
        unit_of_work=unit_of_work
    )
    await cmd_handler.handle(cmd)

    # then
    assert cmd.fields_to_update.name is True
    async with unit_of_work as uow:
        updated_category = await uow.repositories.category.get_by_uuid(category.get_uuid())
        assert updated_category.get_name() == cmd.new_name
        await uow.commit()
