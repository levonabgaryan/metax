import pytest

from metax.core.application.commands_handlers.category import (
    UpdateHelperWordTextCommand,
    UpdateHelperWordTextCommandHandler,
)
from metax_lifespan import MetaxAppLifespanManager
from tests.utils import make_category_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_helper_word_text_command_handler(
    metax_app_for_integration_tests: MetaxAppLifespanManager,
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

    helper_word_to_update = category.get_helper_words()[0]
    helper_word_to_keep = category.get_helper_words()[1]
    cmd = UpdateHelperWordTextCommand(
        category_uuid=category.get_uuid(),
        helper_word_uuid=helper_word_to_update.get_uuid(),
        new_text="updated_helper_word_text",
    )

    # when
    handler = UpdateHelperWordTextCommandHandler(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
    await handler.handle_command(cmd)

    # then
    uow = await unit_of_work_provider.provide()
    async with uow:
        updated_category = await uow.category_repo.get_by_uuid(category.get_uuid())
        updated_words = {word.get_text() for word in updated_category.get_helper_words()}
        assert updated_category.get_name() == category.get_name()
        assert updated_words == {"updated_helper_word_text", helper_word_to_keep.get_text()}
        await uow.commit()
