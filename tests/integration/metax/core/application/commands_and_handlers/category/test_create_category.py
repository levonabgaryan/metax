from uuid import uuid4

import pytest

from metax.core.application.commands_handlers.category import (
    CreateCategoryCommand,
    CreateCategoryCommandHandler,
)
from metax.frameworks_and_drivers.di.metax_container import MetaxContainer


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_create_category_command_handler(
    metax_container_for_integration_tests: MetaxContainer,
) -> None:
    # given
    unit_of_work_provider = (
        metax_container_for_integration_tests.patterns_container.container.unit_of_work_provider()
    )
    event_bus = await metax_container_for_integration_tests.patterns_container.container.event_bus.async_()
    category_uuid = uuid4()
    cmd = CreateCategoryCommand(
        category_uuid=category_uuid,
        name="Test Category",
        helper_words=frozenset(["A", "B"]),
    )

    # when
    cmd_handler_ = CreateCategoryCommandHandler(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
    await cmd_handler_.handle_command(cmd)

    # then
    uow = await unit_of_work_provider.create()
    async with uow:
        category = await uow.category_repo.get_by_uuid(category_uuid)
    assert category.get_uuid() == category_uuid
    assert category.get_name() == cmd.name
    assert category.get_helper_words() == {"B", "A"}
