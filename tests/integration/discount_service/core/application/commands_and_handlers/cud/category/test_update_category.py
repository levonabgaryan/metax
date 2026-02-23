import pytest

from discount_service.core.application.commands_and_handlers.cud.category import (
    UpdateCategoryCommand,
    UpdateCategoryCommandHandler,
)
from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer

from tests.utils import make_category_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_category_command_handler(
    service_container_for_tests: ServiceContainer,
) -> None:
    # given
    unit_of_work = await service_container_for_tests.patterns_container.container.unit_of_work.async_()
    category = make_category_entity()

    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    # when
    cmd = UpdateCategoryCommand(category_uuid=category.get_uuid(), new_name="new_test_name")
    cmd_handler = UpdateCategoryCommandHandler(unit_of_work=unit_of_work)
    await cmd_handler.handle(cmd)

    # then
    assert cmd.fields_to_update.name is True
    async with unit_of_work as uow:
        updated_category = await uow.category_repo.get_by_uuid(category.get_uuid())
        assert updated_category.get_name() == cmd.new_name
        await uow.commit()
