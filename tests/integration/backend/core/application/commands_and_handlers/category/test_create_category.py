from uuid import uuid4

import pytest

from backend.core.application.commands_and_handlers.category import (
    CreateCategoryCommand,
    CreateCategoryCommandHandler,
)
from backend.core.application.ports.patterns.unit_of_work import UnitOfWork


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_create_category_command_handler(unit_of_work: UnitOfWork) -> None:
    # given
    category_uuid = uuid4()
    cmd = CreateCategoryCommand(
        category_uuid=category_uuid,
        name="Test Category",
        helper_words=frozenset(["A", "B"]),
    )

    # when
    await CreateCategoryCommandHandler(unit_of_work=unit_of_work).handle(cmd)

    # then
    category = await unit_of_work.repositories.category.get_by_uuid(category_uuid)
    assert category.get_uuid() == category_uuid
    assert category.get_name() == cmd.name
    assert category.get_helper_words() == cmd.helper_words
