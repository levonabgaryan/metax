import pytest

from metax.core.application.commands_handlers.category import (
    UpdateCategoryCommand,
    UpdateCategoryCommandHandler,
)
from metax_application import MetaxApplication
from tests.utils import make_category_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_category_command_handler(
    metax_app_for_integration_tests: MetaxApplication,
) -> None:
    # given
    metax_container_for_integration_tests = metax_app_for_integration_tests.get_di_container()
    unit_of_work_provider = (
        metax_container_for_integration_tests.patterns_container.container.unit_of_work_provider()
    )
    event_bus = await metax_container_for_integration_tests.patterns_container.container.event_bus.async_()
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()
    category = make_category_entity()

    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    initial_helper_words = category.get_helper_words()

    # when
    cmd = UpdateCategoryCommand(category_uuid=category.get_uuid(), new_name="new_test_name")
    cmd_handler = UpdateCategoryCommandHandler(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
    await cmd_handler.handle_command(cmd)

    # then
    uow = await unit_of_work_provider.create()
    async with uow:
        updated_category = await uow.category_repo.get_by_uuid(category.get_uuid())
        assert updated_category.get_name() == cmd.new_name
        assert updated_category.get_helper_words() == initial_helper_words
        await uow.commit()
