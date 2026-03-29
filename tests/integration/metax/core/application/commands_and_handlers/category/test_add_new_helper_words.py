import pytest

from metax.core.application.commands_handlers.category.add_new_helper_words import (
    AddNewHelperWordsCommand,
    AddNewHelperWordsCommandHandler,
)
from metax.core.domain.entities.category.value_objects import CategoryHelperWords
from metax.frameworks_and_drivers.di.metax_container import MetaxContainer
from tests.utils import make_category_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_add_new_helper_word_command(metax_container_for_integration_tests: MetaxContainer) -> None:
    # given
    unit_of_work_provider = (
        await metax_container_for_integration_tests.patterns_container.container.unit_of_work_provider.async_()
    )
    event_bus = metax_container_for_integration_tests.patterns_container.container.event_bus()
    unit_of_work = await metax_container_for_integration_tests.patterns_container.container.unit_of_work.async_()
    helper_words = CategoryHelperWords(words=frozenset(["a", "b"]))
    category = make_category_entity(
        helper_words=helper_words,
    )
    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    cmd = AddNewHelperWordsCommand(category_uuid=category.get_uuid(), new_helper_words=frozenset(["c", "d"]))

    expected_helper_words = CategoryHelperWords(words=frozenset(["a", "b", "c", "d"]))
    # when
    cmd_handler = AddNewHelperWordsCommandHandler(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
    await cmd_handler.handle_command(cmd)

    # then
    uow_read = await unit_of_work_provider.create()
    async with uow_read:
        updated_category = await uow_read.category_repo.get_by_uuid(category.get_uuid())

    assert updated_category.get_helper_words() == expected_helper_words.words
