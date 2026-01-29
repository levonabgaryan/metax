import pytest
from dependency_injector.wiring import Provide, inject

from discount_service.core.application.commands_and_handlers.cud.category.delete_helper_words import (
    DeleteHelperWordsCommand,
    DeleteHelperWordsCommandHandler,
)
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.core.domain.entities.category_entity.category import CategoryHelperWords
from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer
from tests.utils import make_category_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@inject
async def test_delete_helper_word_command(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
    command_handler: DeleteHelperWordsCommandHandler = Provide[
        ServiceContainer.commands_handlers_container.container.category.container.delete_helper_words
    ],
) -> None:
    # given
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
    cmd_handler = command_handler
    await cmd_handler.handle(cmd)

    # then
    updated_category = await uow.category_repo.get_by_uuid(category.get_uuid())

    assert updated_category.get_helper_words() == expected_helper_words.words
