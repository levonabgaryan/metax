from dependency_injector import providers, containers

from backend.core.application.commands_and_handlers.category import (
    CreateCategoryCommandHandler,
    UpdateCategoryCommandHandler,
    CreateCategoryCommand,
    UpdateCategoryCommand,
)
from backend.core.application.commands_and_handlers.retailer import (
    CreateRetailerCommandHandler,
    UpdateRetailerCommandHandler,
    CreateRetailerCommand,
    UpdateRetailerCommand,
)
from backend.core.application.patterns.command_handler_abc import CommandHandler
from backend.frameworks_and_drivers.di.patterns_container import PatternsContainer


class CategoryCommandHandlersContainer(containers.DeclarativeContainer):
    patterns: providers.Container[PatternsContainer] = providers.Container(PatternsContainer)

    create_category: providers.Provider[CommandHandler[CreateCategoryCommand]] = providers.Factory(
        CreateCategoryCommandHandler,
        unit_of_work=patterns.unit_of_work,
    )

    update_category: providers.Provider[CommandHandler[UpdateCategoryCommand]] = providers.Factory(
        UpdateCategoryCommandHandler, unit_of_work=patterns.unit_of_work
    )


class RetailerCommandHandlersContainer(containers.DeclarativeContainer):
    patterns: providers.Container[PatternsContainer] = providers.Container(PatternsContainer)

    create_retailer: providers.Provider[CommandHandler[CreateRetailerCommand]] = providers.Factory(
        CreateRetailerCommandHandler,
        unit_of_work=patterns.unit_of_work,
    )

    update_retailer: providers.Provider[CommandHandler[UpdateRetailerCommand]] = providers.Factory(
        UpdateRetailerCommandHandler,
        unit_of_work=patterns.unit_of_work,
    )


class CommandHandlersContainer(containers.DeclarativeContainer):
    category: providers.Container[CategoryCommandHandlersContainer] = providers.Container(
        CategoryCommandHandlersContainer
    )
    retailer: providers.Container[RetailerCommandHandlersContainer] = providers.Container(
        RetailerCommandHandlersContainer
    )
