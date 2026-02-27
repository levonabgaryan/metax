import pytest

from discount_service.core.application.commands_handlers.category.delete_helper_words import (
    DeleteHelperWordsCommand,
    DeleteHelperWordsCommandHandler,
)
from discount_service.core.domain.entities.category_entity.category import CategoryHelperWords
from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer
from tests.utils import make_category_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_delete_helper_word_command(
    service_container_for_tests: ServiceContainer,
) -> None:
    # given
    unit_of_work = await service_container_for_tests.patterns_container.container.unit_of_work.async_()
    event_bus = await service_container_for_tests.patterns_container.container.event_bus.async_()
    helper_words = CategoryHelperWords(words=frozenset(["a", "b", "c", "d"]))
    category = make_category_entity(
        helper_words=helper_words,
    )
    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    cmd = DeleteHelperWordsCommand(category_uuid=category.get_uuid(), words_to_delete=frozenset(["a", "b", "c"]))

    expected_helper_words = CategoryHelperWords(words=frozenset(["d"]))
    # when
    cmd_handler = DeleteHelperWordsCommandHandler(unit_of_work=unit_of_work, event_bus=event_bus)
    await cmd_handler.handle_command(cmd)

    # then
    updated_category = await uow.category_repo.get_by_uuid(category.get_uuid())

    assert updated_category.get_helper_words() == expected_helper_words.words
