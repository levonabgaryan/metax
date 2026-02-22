from dependency_injector import containers, providers

from discount_service.core.application.patterns.category_classifier_service import CategoryClassifierService
from discount_service.core.application.patterns.message_buss import MessageBus
from discount_service.core.application.ports.patterns.factories.unit_of_work_factory import IUnitOfWorkFactory
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.frameworks_and_drivers.patterns.factories.unit_of_work_factory import DjangoUnitOfWorkFactory
from discount_service.frameworks_and_drivers.patterns.unit_of_work import UnitOfWork


class PatternsContainer(containers.DeclarativeContainer):
    repositories_container: providers.DependenciesContainer = providers.DependenciesContainer()
    discounted_products_collector_services_container: providers.DependenciesContainer = (
        providers.DependenciesContainer()
    )
    unit_of_work: providers.Factory[AbstractUnitOfWork] = providers.Factory(
        UnitOfWork,
        discounted_product_repo=repositories_container.discounted_product_repository,
        retailer_repo=repositories_container.retailer_repository,
        category_repo=repositories_container.category_repository,
        discounted_product_read_model_repo=repositories_container.discounted_product_read_model_repository,
    )
    unit_of_work_factory: providers.Factory[IUnitOfWorkFactory] = providers.Factory(
        DjangoUnitOfWorkFactory, unit_of_work_provider=unit_of_work.provider
    )
    message_bus: providers.ThreadSafeSingleton[MessageBus] = providers.ThreadSafeSingleton(MessageBus, unit_of_work_factory)
    category_classifier_service: providers.Factory[CategoryClassifierService] = providers.Factory(
        CategoryClassifierService, unit_of_work=unit_of_work
    )