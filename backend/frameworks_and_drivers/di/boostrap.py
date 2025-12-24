from dependency_injector import containers, providers

from backend.frameworks_and_drivers.di.command_handlers_container import CommandHandlersContainer
from backend.frameworks_and_drivers.di.patterns_container import PatternsContainer
from backend.frameworks_and_drivers.di.use_cases_container import UseCasesContainer


class MainContainer(containers.DeclarativeContainer):
    config: providers.Configuration = providers.Configuration()

    patterns: providers.Container[PatternsContainer] = providers.Container(PatternsContainer)
    command_handlers: providers.Container[CommandHandlersContainer] = providers.Container(CommandHandlersContainer)
    use_cases: providers.Container[UseCasesContainer] = providers.Container(UseCasesContainer)


main_container = MainContainer()
