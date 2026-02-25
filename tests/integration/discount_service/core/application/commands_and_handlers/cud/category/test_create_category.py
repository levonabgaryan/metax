from uuid import uuid4

import pytest

from discount_service.core.application.commands_handlers.category import (
    CreateCategoryCommand,
    CreateCategoryCommandHandler,
)
from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_create_category_command_handler(
    service_container_for_tests: ServiceContainer,
) -> None:
    # given
    unit_of_work = await service_container_for_tests.patterns_container.container.unit_of_work.async_()
    event_bus = await service_container_for_tests.patterns_container.container.event_bus.async_()
    category_uuid = uuid4()
    cmd = CreateCategoryCommand(
        category_uuid=category_uuid,
        name="Test Category",
        helper_words=frozenset(["A", "B"]),
    )

    # when
    cmd_handler_ = CreateCategoryCommandHandler(unit_of_work=unit_of_work, mediator=event_bus)
    await cmd_handler_.handle_command(cmd)

    # then
    category = await unit_of_work.category_repo.get_by_uuid(category_uuid)
    assert category.get_uuid() == category_uuid
    assert category.get_name() == cmd.name
    assert category.get_helper_words() == {"B", "A"}
