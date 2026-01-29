from uuid import uuid4

import pytest
from dependency_injector.wiring import Provide, inject

from discount_service.core.application.commands_and_handlers.cud.category import (
    CreateCategoryCommand,
    CreateCategoryCommandHandler,
)
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@inject
async def test_create_category_command_handler(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
    cmd_handler: CreateCategoryCommandHandler = Provide[
        ServiceContainer.commands_handlers_container.container.category.container.create_category
    ],
) -> None:
    # given
    category_uuid = uuid4()
    cmd = CreateCategoryCommand(
        category_uuid=category_uuid,
        name="Test Category",
        helper_words=frozenset(["A", "B"]),
    )

    # when
    cmd_handler_ = cmd_handler
    await cmd_handler_.handle(cmd)

    # then
    category = await unit_of_work.category_repo.get_by_uuid(category_uuid)
    assert category.get_uuid() == category_uuid
    assert category.get_name() == cmd.name
    assert category.get_helper_words() == cmd.helper_words
