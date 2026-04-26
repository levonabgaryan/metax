import pytest

from metax.core.application.commands_handlers.category import (
    AddNewHelperWordsCommand,
    AddNewHelperWordsCommandHandler,
)
from metax.core.application.commands_handlers.category.add_new_helper_words import HelperWordPayload
from metax_lifespan import MetaxAppLifespanManager
from tests.utils import make_category_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_add_new_helper_words_command(metax_app_for_integration_tests: MetaxAppLifespanManager) -> None:
    di_container = metax_app_for_integration_tests.get_di_container()
    unit_of_work_provider = di_container.patterns_container.container.unit_of_work_provider()
    event_bus = await di_container.patterns_container.container.event_bus.async_()
    unit_of_work = di_container.patterns_container.container.unit_of_work()
    category = make_category_entity()
    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    command = AddNewHelperWordsCommand(
        category_uuid=category.get_uuid(),
        new_helper_words=[HelperWordPayload(text="c"), HelperWordPayload(text="d")],
    )
    handler = AddNewHelperWordsCommandHandler(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
    await handler.handle_command(command)

    async with unit_of_work as uow:
        updated_category = await uow.category_repo.get_by_uuid(category.get_uuid())

    assert {word.get_text() for word in updated_category.get_helper_words()} == {
        "test_word1",
        "test_word2",
        "c",
        "d",
    }
