from dependency_injector import containers, providers

from backend.frameworks_and_drivers.presenters.rest_presenters.category import (
    CategoryViewModel,
    CategoryResponse,
    RestCategoryPresenter,
)
from backend.frameworks_and_drivers.presenters.rest_presenters.discounted_product import (
    DiscountedProductViewModel,
    DiscountedProductResponse,
    RestDiscountedProductPresenter,
)
from backend.frameworks_and_drivers.presenters.rest_presenters.retailer import (
    RetailerViewModel,
    RetailerResponse,
    RestRetailerPresenter,
)
from backend.interface_adapters.ports.presenters.base_presenter import BasePresenter


class PresentersContainer(containers.DeclarativeContainer):
    category_presenter: providers.Provider[BasePresenter[CategoryViewModel, CategoryResponse]] = providers.Factory(
        RestCategoryPresenter
    )
    retailer_presenter: providers.Provider[BasePresenter[RetailerViewModel, RetailerResponse]] = providers.Factory(
        RestRetailerPresenter
    )
    discounted_product_presenter: providers.Provider[
        BasePresenter[DiscountedProductViewModel, DiscountedProductResponse]
    ] = providers.Factory(RestDiscountedProductPresenter)
