from dependency_injector import containers, providers

from backend.core.application.patterns.message_buss import MessageBus
from backend.core.application.patterns.unit_of_work_factory import IUnitOfWorkFactory
from backend.core.application.ports.patterns.unit_of_work import UnitOfWork
from backend.frameworks_and_drivers.di.repositories_container import RepositoriesContainer
from backend.frameworks_and_drivers.patterns.unit_of_work import DjangoUnitOfWork
from backend.frameworks_and_drivers.patterns.unit_of_work_factory import DjangoUnitOfWorkFactory


class PatternsContainer(containers.DeclarativeContainer):
    repos = providers.Container(RepositoriesContainer)

    unit_of_work: providers.Provider[UnitOfWork] = providers.Factory(
        DjangoUnitOfWork,
        category_repo=repos.category_repository,
        retailer_repo=repos.retailer_repository,
        discounted_product_repo=repos.discounted_product_repository,
    )
    unit_of_work_factory: providers.Provider[IUnitOfWorkFactory] = providers.ThreadSafeSingleton(
        DjangoUnitOfWorkFactory
    )
    message_bus: providers.Provider[MessageBus] = providers.ThreadSafeSingleton(
        MessageBus, unit_of_work_factory=unit_of_work_factory
    )

    # discounted_product_factory
