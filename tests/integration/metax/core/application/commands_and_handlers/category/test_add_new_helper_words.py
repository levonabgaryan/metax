import pytest

from metax.core.application.commands_handlers.category.add_new_helper_words import (
    AddNewHelperWordsCommand,
    AddNewHelperWordsCommandHandler,
)
from metax.core.domain.entities.category.value_objects import CategoryHelperWords
from metax.frameworks_and_drivers.di.bootstrap import MetaxContainer
from tests.utils import make_category_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_add_new_helper_word_command(service_container_for_integration_tests: MetaxContainer) -> None:
    # given
    unit_of_work = await service_container_for_integration_tests.patterns_container.container.unit_of_work.async_()
    event_bus = service_container_for_integration_tests.patterns_container.container.event_bus()
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
    cmd_handler = AddNewHelperWordsCommandHandler(unit_of_work=unit_of_work, event_bus=event_bus)
    await cmd_handler.handle_command(cmd)

    # then
    updated_category = await uow.category_repo.get_by_uuid(category.get_uuid())

    assert updated_category.get_helper_words() == expected_helper_words.words
