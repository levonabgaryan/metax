import pytest
from dependency_injector.wiring import inject, Provide

from discount_service.core.application.commands_and_handlers.cud.category.add_new_helper_words import (
    AddNewHelperWordsCommand,
    AddNewHelperWordsCommandHandler,
)
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.core.domain.entities.category_entity.category import CategoryHelperWords
from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer
from tests.utils import make_category_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@inject
async def test_add_new_helper_word_command(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
    command_handler: AddNewHelperWordsCommandHandler = Provide[
        ServiceContainer.commands_handlers_container.container.category.container.add_new_helper_words
    ],
) -> None:
    # given

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
    cmd_handler = command_handler
    await cmd_handler.handle(cmd)

    # then
    updated_category = await uow.category_repo.get_by_uuid(category.get_uuid())

    assert updated_category.get_helper_words() == expected_helper_words.words
