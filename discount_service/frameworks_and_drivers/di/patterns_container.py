from __future__ import annotations
from dependency_injector import containers, providers

from discount_service.core.application.patterns.event_bus import EventBus
from discount_service.core.application.patterns.mediator import Mediator
from discount_service.core.application.patterns.services.category_classifier_service import (
    CategoryClassifierService,
)
from discount_service.core.application.event_handlers.category.events import CategoryUpdated
from discount_service.core.application.event_handlers.category.update_in_discounted_product_read_model import (
    UpdateCategoryInDiscountedProductReadModel,
)
from discount_service.core.application.event_handlers.discounted_product.delete_old_discounted_products import (
    DeleteOldDiscountedProducts,
)
from discount_service.core.application.event_handlers.discounted_product.events import (
    NewDiscountedProductsFromRetailerCollected,
    OldDiscountedProductsDeleted,
)
from discount_service.core.application.event_handlers.discounted_product.sync_discounted_products_read_model import (
    SyncDiscountedProductReadModel,
)
from discount_service.core.application.event_handlers.retailer.events import RetailerUpdated
from discount_service.core.application.event_handlers.retailer.update_in_discounted_product_read_model import (
    UpdateRetailerInDiscountedProductReadModel,
)
from discount_service.core.application.patterns.event_handler_abc import EventHandler
from discount_service.core.application.ports.patterns.factories.unit_of_work_factory import IUnitOfWorkFactory
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.frameworks_and_drivers.patterns.factories.unit_of_work_factory import DjangoUnitOfWorkFactory
from discount_service.frameworks_and_drivers.patterns.unit_of_work import UnitOfWork


class PatternsContainer(containers.DeclarativeContainer):
    repositories_container: providers.DependenciesContainer = providers.DependenciesContainer()
    discounted_products_collector_services_container: providers.DependenciesContainer = (
        providers.DependenciesContainer()
    )
    event_handlers_container: providers.DependenciesContainer = providers.DependenciesContainer()
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
    category_classifier_service: providers.Factory[CategoryClassifierService] = providers.Factory(
        CategoryClassifierService, unit_of_work=unit_of_work
    )

    update_category_in_discounted_product_read_model_event_handler: providers.Factory[
        EventHandler[CategoryUpdated]
    ] = providers.Factory(
        UpdateCategoryInDiscountedProductReadModel,
        unit_of_work=unit_of_work,
    )
    update_retailer_in_discounted_product_read_model_event_handler: providers.Factory[
        EventHandler[RetailerUpdated]
    ] = providers.Factory(
        UpdateRetailerInDiscountedProductReadModel,
        unit_of_work=unit_of_work,
    )
    delete_old_discounted_products_event_handler: providers.Factory[
        EventHandler[NewDiscountedProductsFromRetailerCollected]
    ] = providers.Factory(
        DeleteOldDiscountedProducts,
        unit_of_work=unit_of_work,
    )
    sync_discounted_products_in_read_model_event_handler: providers.Factory[
        EventHandler[OldDiscountedProductsDeleted]
    ] = providers.Factory(
        SyncDiscountedProductReadModel,
        unit_of_work=unit_of_work,
    )

    event_bus: providers.ThreadSafeSingleton[Mediator] = providers.ThreadSafeSingleton(
        EventBus,
        update_category_in_discounted_product_read_model_event_handler=update_category_in_discounted_product_read_model_event_handler,
        update_retailer_in_discounted_product_read_model_event_handler=update_retailer_in_discounted_product_read_model_event_handler,
        delete_old_discounted_products_event_handler=delete_old_discounted_products_event_handler,
        sync_discounted_products_in_read_model_event_handler=sync_discounted_products_in_read_model_event_handler,
    )
