from dependency_injector import containers, providers

from backend.frameworks_and_drivers.di.commands_handlers_container import CommandsHandlersContainer
from backend.frameworks_and_drivers.di.event_handlers_container import EventHandlersContainer
from backend.frameworks_and_drivers.di.patterns_container import PatternsContainer
from backend.frameworks_and_drivers.di.repositories_container import RepositoriesContainer
from backend.frameworks_and_drivers.di.use_cases_container import UseCasesContainer


class MainContainer(containers.DeclarativeContainer):
    config: providers.Configuration = providers.Configuration()

    repositories: providers.Container[RepositoriesContainer] = providers.Container(RepositoriesContainer)

    patterns: providers.Container[PatternsContainer] = providers.Container(
        PatternsContainer, repositories=repositories
    )
    commands_handlers: providers.Container[CommandsHandlersContainer] = providers.Container(
        CommandsHandlersContainer, patterns=patterns
    )
    event_handlers: providers.Container[EventHandlersContainer] = providers.Container(
        EventHandlersContainer, patterns=patterns
    )
    use_cases: providers.Container[UseCasesContainer] = providers.Container(UseCasesContainer, patterns=patterns)


main_container = MainContainer()
