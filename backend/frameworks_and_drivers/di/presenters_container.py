from dependency_injector import containers, providers

from backend.frameworks_and_drivers.presenters.pydantic_presenters.category_presenter_and_schemas.presenter import (
    CategoryViewModel,
    CategoryResponse,
    RestCategoryPresenter,
)
from backend.frameworks_and_drivers.presenters.pydantic_presenters.discounted_product_presenter_and_schemas.presenter import (
    DiscountedProductViewModel,
    DiscountedProductResponse,
    RestDiscountedProductPresenter,
)
from backend.frameworks_and_drivers.presenters.pydantic_presenters.retailer_presenter_and_schemas.presenter import (
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
