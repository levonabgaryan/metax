from dependency_injector import containers, providers

from backend.frameworks_and_drivers.di.patterns_container import PatternsContainer


class MainContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    patterns = providers.Container(PatternsContainer)
