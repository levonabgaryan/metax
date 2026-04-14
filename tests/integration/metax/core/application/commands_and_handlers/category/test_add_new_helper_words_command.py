import pytest

from metax.core.application.commands_handlers.category import (
    AddNewHelperWordsCommand,
    AddNewHelperWordsCommandHandler,
)
from metax.core.domain.entities.category.value_objects import CategoryHelperWords
from metax_application_manager import MetaxApplicationManager
from tests.utils import make_category_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_add_new_helper_words_command(metax_app_for_integration_tests: MetaxApplicationManager) -> None:
    di_container = metax_app_for_integration_tests.get_di_container()
    unit_of_work_provider = di_container.patterns_container.container.unit_of_work_provider()
    event_bus = await di_container.patterns_container.container.event_bus.async_()
    unit_of_work = di_container.patterns_container.container.unit_of_work()
    helper_words = CategoryHelperWords.create(words=frozenset(["a", "b"]))
    category = make_category_entity(
        helper_words=helper_words,
    )
    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    command = AddNewHelperWordsCommand(category_uuid=category.get_uuid(), new_helper_words=frozenset(["c", "d"]))

    expected_helper_words = CategoryHelperWords.create(words=frozenset(["a", "b", "c", "d"]))
    handler = AddNewHelperWordsCommandHandler(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
    await handler.handle_command(command)

    async with unit_of_work as uow:
        updated_category = await uow.category_repo.get_by_uuid(category.get_uuid())

    assert updated_category.get_helper_words() == expected_helper_words.words
