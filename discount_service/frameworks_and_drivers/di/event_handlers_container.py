from dependency_injector import containers, providers

from discount_service.core.application.event_and_handlers.category.update_in_discounted_product_read_model import (
    UpdateCategoryInDiscountedProductReadModel,
)
from discount_service.core.application.event_and_handlers.discounted_product.delete_old_discounted_products import (
    DeleteOldDiscountedProducts,
)
from discount_service.core.application.event_and_handlers.discounted_product.events import (
    NewDiscountedProductsFromRetailerCollected,
    OldDiscountedProductsDeleted,
)
from discount_service.core.application.event_and_handlers.discounted_product.sync_discounted_products_read_model import (
    SyncDiscountedProductReadModel,
)
from discount_service.core.application.event_and_handlers.retailer.update_in_discounted_product_read_model import (
    UpdateRetailerInDiscountedProductReadModel,
)
from discount_service.core.application.patterns.event_handler_abc import EventHandler
from discount_service.core.domain.entities.category_entity.events import CategoryUpdated
from discount_service.core.domain.entities.retailer_entity.events import RetailerUpdated


class DiscountedProductEventHandlersContainer(containers.DeclarativeContainer):
    patterns: providers.DependenciesContainer = providers.DependenciesContainer()

    delete_old_discounted_products: providers.Provider[
        EventHandler[NewDiscountedProductsFromRetailerCollected]
    ] = providers.Factory(DeleteOldDiscountedProducts, unit_of_work=patterns.unit_of_work)
    sync_discounted_product_read_model: providers.Provider[EventHandler[OldDiscountedProductsDeleted]] = (
        providers.Factory(SyncDiscountedProductReadModel, unit_of_work=patterns.unit_of_work)
    )


class RetailerEventHandlersContainer(containers.DeclarativeContainer):
    patterns: providers.DependenciesContainer = providers.DependenciesContainer()

    update_discounted_product_read_model: providers.Provider[EventHandler[RetailerUpdated]] = providers.Factory(
        UpdateRetailerInDiscountedProductReadModel, unit_of_work=patterns.unit_of_work
    )


class CategoryEventHandlersContainer(containers.DeclarativeContainer):
    patterns: providers.DependenciesContainer = providers.DependenciesContainer()

    update_discounted_product_read_model: providers.Provider[EventHandler[CategoryUpdated]] = providers.Factory(
        UpdateCategoryInDiscountedProductReadModel, unit_of_work=patterns.unit_of_work
    )


class EventHandlersContainer(containers.DeclarativeContainer):
    patterns: providers.DependenciesContainer = providers.DependenciesContainer()

    category: providers.Container[CategoryEventHandlersContainer] = providers.Container(
        CategoryEventHandlersContainer,
        patterns=patterns,
    )
    retailer: providers.Container[RetailerEventHandlersContainer] = providers.Container(
        RetailerEventHandlersContainer, patterns=patterns
    )
    discounted_product: providers.Container[DiscountedProductEventHandlersContainer] = providers.Container(
        DiscountedProductEventHandlersContainer, patterns=patterns
    )
