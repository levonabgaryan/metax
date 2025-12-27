from dependency_injector import providers, containers

from backend.core.application.commands_and_handlers.cud.category import (
    CreateCategoryCommandHandler,
    UpdateCategoryCommandHandler,
    CreateCategoryCommand,
    UpdateCategoryCommand,
)
from backend.core.application.commands_and_handlers.cud.retailer import (
    CreateRetailerCommandHandler,
    UpdateRetailerCommandHandler,
    CreateRetailerCommand,
    UpdateRetailerCommand,
)
from backend.core.application.commands_and_handlers.cud.category.add_new_helper_words import (
    AddNewHelperWordsCommand,
    AddNewHelperWordsCommandHandler,
)
from backend.core.application.commands_and_handlers.cud.category.delete_helper_words import (
    DeleteHelperWordsCommand,
    DeleteHelperWordsCommandHandler,
)
from backend.core.application.patterns.command_handler_abc import CommandHandler
from backend.frameworks_and_drivers.di.patterns_container import PatternsContainer


class CategoryCommandsHandlersContainer(containers.DeclarativeContainer):
    patterns: providers.Container[PatternsContainer] = providers.Container(PatternsContainer)

    create_category: providers.Provider[CommandHandler[CreateCategoryCommand]] = providers.Factory(
        CreateCategoryCommandHandler,
        unit_of_work=patterns.unit_of_work,
    )

    update_category: providers.Provider[CommandHandler[UpdateCategoryCommand]] = providers.Factory(
        UpdateCategoryCommandHandler, unit_of_work=patterns.unit_of_work
    )

    # use cases commands handlers
    add_new_helper_words: providers.Provider[CommandHandler[AddNewHelperWordsCommand]] = providers.Factory(
        AddNewHelperWordsCommandHandler, unit_of_work=patterns.unit_of_work
    )

    delete_helper_words: providers.Provider[CommandHandler[DeleteHelperWordsCommand]] = providers.Factory(
        DeleteHelperWordsCommandHandler, unit_of_work=patterns.unit_of_work
    )


class RetailerCommandsHandlersContainer(containers.DeclarativeContainer):
    patterns: providers.Container[PatternsContainer] = providers.Container(PatternsContainer)

    create_retailer: providers.Provider[CommandHandler[CreateRetailerCommand]] = providers.Factory(
        CreateRetailerCommandHandler,
        unit_of_work=patterns.unit_of_work,
    )

    update_retailer: providers.Provider[CommandHandler[UpdateRetailerCommand]] = providers.Factory(
        UpdateRetailerCommandHandler,
        unit_of_work=patterns.unit_of_work,
    )


class CommandsHandlersContainer(containers.DeclarativeContainer):
    category: providers.Container[CategoryCommandsHandlersContainer] = providers.Container(
        CategoryCommandsHandlersContainer
    )
    retailer: providers.Container[RetailerCommandsHandlersContainer] = providers.Container(
        RetailerCommandsHandlersContainer
    )
