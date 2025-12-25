from dependency_injector import containers, providers

from backend.frameworks_and_drivers.di.commands_handlers_container import CommandsHandlersContainer
from backend.frameworks_and_drivers.di.patterns_container import PatternsContainer
from backend.frameworks_and_drivers.di.presenters_container import PresentersContainer
from backend.frameworks_and_drivers.di.use_cases_container import UseCasesContainer
from backend.interface_adapters.controllers.category import CategoryController
from backend.interface_adapters.controllers.retailer import RetailerController


class ControllersContainer(containers.DeclarativeContainer):
    patterns = providers.Container(PatternsContainer)
    cmds_handlers = providers.Container(CommandsHandlersContainer)
    use_cases = providers.Container(UseCasesContainer)
    presenters = providers.Container(PresentersContainer)

    category_controller: providers.Provider[CategoryController] = providers.Factory(
        CategoryController,
        message_bus=patterns().message_bus,
        create_category_cmd_handler=cmds_handlers().category().create_category,
        add_new_helper_words_use_case=use_cases().category().add_new_helper_words,
        delete_helper_words_use_case=use_cases().category().delete_helper_words,
        category_presenter=presenters().category_presenter,
    )

    retailer_controller: providers.Provider[RetailerController] = providers.Factory(
        RetailerController, message_bus=patterns().message_bus, retailer_presenter=presenters().retailer_presenter
    )

    # discounted_product_controller: providers.Provider[DiscountedProduct]
