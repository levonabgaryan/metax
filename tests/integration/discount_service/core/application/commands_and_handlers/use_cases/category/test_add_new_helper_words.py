import pytest

from discount_service.core.application.commands_and_handlers.cud.category.add_new_helper_words import (
    AddNewHelperWordsCommand,
)
from discount_service.core.application.patterns.command_handler_abc import CommandHandler
from discount_service.core.application.ports.patterns.unit_of_work import UnitOfWork
from discount_service.core.domain.entities.category_entity.category import CategoryHelperWords
from discount_service.frameworks_and_drivers.di.commands_handlers_container import (
    CategoryCommandsHandlersContainer,
)
from tests.integration.conftest import make_category_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_add_new_helper_word_command(
    unit_of_work: UnitOfWork, category_commands_handlers: CategoryCommandsHandlersContainer
) -> None:
    # given
    helper_words = CategoryHelperWords(words=frozenset(["a", "b"]))
    category = make_category_entity(
        helper_words=helper_words,
    )
    async with unit_of_work as uow:
        await uow.repositories.category.add(category)
        await uow.commit()

    cmd = AddNewHelperWordsCommand(category_uuid=category.get_uuid(), new_helper_words=frozenset(["c", "d"]))

    expected_helper_words = CategoryHelperWords(words=frozenset(["a", "b", "c", "d"]))
    # when
    cmd_handler: CommandHandler[AddNewHelperWordsCommand] = category_commands_handlers.add_new_helper_words(
        unit_of_work=unit_of_work
    )
    await cmd_handler.handle(cmd)

    # then
    async with unit_of_work as uow:
        updated_category = await uow.repositories.category.get_by_uuid(category.get_uuid())
        await uow.commit()

    assert updated_category.get_helper_words() == expected_helper_words.words
