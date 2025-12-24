from dependency_injector import containers, providers

from backend.core.application.patterns.message_buss import MessageBus
from backend.core.application.input_ports.patterns.unit_of_work import UnitOfWork
from backend.core.application.patterns.unit_of_work_factory import IUnitOfWorkFactory
from backend.frameworks_and_drivers.di.repositories_container import RepositoriesContainer
from backend.frameworks_and_drivers.patterns.unit_of_work import DjangoUnitOfWork
from backend.frameworks_and_drivers.patterns.unit_of_work_factory import DjangoUnitOfWorkFactory


class PatternsContainer(containers.DeclarativeContainer):
    repositories: providers.Container[RepositoriesContainer] = providers.Container(RepositoriesContainer)

    unit_of_work: providers.Provider[UnitOfWork] = providers.Factory(
        DjangoUnitOfWork,
        category_repository=repositories.category_repository,
        retailer_repository=repositories.retailer_repository,
        discounted_product_repository=repositories.discounted_product_repository,
    )

    unit_of_work_factory: providers.Provider[IUnitOfWorkFactory] = providers.Factory(
        DjangoUnitOfWorkFactory, unit_of_work_provider=unit_of_work.provider
    )

    message_bus: providers.Provider[MessageBus] = providers.ThreadSafeSingleton(MessageBus, unit_of_work_factory)
