from dependency_injector import containers, providers
from opensearchpy import AsyncOpenSearch

from discount_service.core.application.ports.patterns.discounted_product_factory import IDiscountedProductFactory
from discount_service.core.application.patterns.message_buss import MessageBus
from discount_service.core.application.ports.patterns.repositories_abstract_factory import (
    IRepositoriesAbstractFactory,
)
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.core.application.ports.patterns.unit_of_work_factory import IUnitOfWorkFactory
from discount_service.frameworks_and_drivers.patterns.discounted_product_factory import DiscountedProductFactory
from discount_service.frameworks_and_drivers.patterns.repositories_factory import RepositoriesAbstractFactory
from discount_service.frameworks_and_drivers.patterns.unit_of_work import UnitOfWork
from discount_service.frameworks_and_drivers.patterns.unit_of_work_factory import DjangoUnitOfWorkFactory


class PatternsContainer(containers.DeclarativeContainer):
    opensearch_async_client: providers.Dependency[AsyncOpenSearch] = providers.Dependency(
        instance_of=AsyncOpenSearch
    )
    repositories_abstract_factory: providers.Provider[IRepositoriesAbstractFactory] = (
        providers.ThreadSafeSingleton(RepositoriesAbstractFactory, opensearch_async_client=opensearch_async_client)
    )

    unit_of_work: providers.Provider[AbstractUnitOfWork] = providers.Factory(
        UnitOfWork, repositories_abstract_factory=repositories_abstract_factory
    )

    unit_of_work_factory: providers.Provider[IUnitOfWorkFactory] = providers.Factory(
        DjangoUnitOfWorkFactory, unit_of_work_provider=unit_of_work.provider
    )

    message_bus: providers.Provider[MessageBus] = providers.ThreadSafeSingleton(MessageBus, unit_of_work_factory)

    discounted_product_factory: providers.Provider[IDiscountedProductFactory] = providers.Factory(
        DiscountedProductFactory,
    )
