import pytest

from backend.core.application.commands_and_handlers.category import (
    UpdateCategoryCommand,
    UpdateCategoryCommandHandler,
)
from backend.core.application.ports.patterns.unit_of_work import UnitOfWork
from tests.integration.conftest import make_category_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_category_command_handler(unit_of_work: UnitOfWork) -> None:
    # given
    category = make_category_entity()

    async with unit_of_work as uow:
        await uow.repositories.category.add(category)
        await uow.commit()

    # when
    cmd = UpdateCategoryCommand(category_uuid=category.get_uuid(), new_name="new_test_name")
    await UpdateCategoryCommandHandler(unit_of_work).handle(cmd)

    # then
    assert cmd.fields_to_update.name is True
    async with unit_of_work as uow:
        updated_category = await uow.repositories.category.get_by_uuid(category.get_uuid())
        assert updated_category.get_name() == cmd.new_name
        await uow.commit()
