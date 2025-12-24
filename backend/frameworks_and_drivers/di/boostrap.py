from dependency_injector import containers, providers

from backend.frameworks_and_drivers.di.commands_handlers_container import CommandsHandlersContainer
from backend.frameworks_and_drivers.di.patterns_container import PatternsContainer
from backend.frameworks_and_drivers.di.use_cases_container import UseCasesContainer


class MainContainer(containers.DeclarativeContainer):
    config: providers.Configuration = providers.Configuration()

    patterns: providers.Container[PatternsContainer] = providers.Container(PatternsContainer)
    commands_handlers: providers.Container[CommandsHandlersContainer] = providers.Container(
        CommandsHandlersContainer
    )
    use_cases: providers.Container[UseCasesContainer] = providers.Container(UseCasesContainer)


main_container = MainContainer()
