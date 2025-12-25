from dependency_injector import containers, providers

from backend.frameworks_and_drivers.presenters.pydantic_presenters.category_presenter_and_schemas.presenter import (
    CategoryViewModel,
    CategoryResponse,
    PydanticCategoryPresenter,
)
from backend.frameworks_and_drivers.presenters.pydantic_presenters.discounted_product_presenter_and_schemas.presenter import (
    DiscountedProductViewModel,
    DiscountedProductResponse,
    PydanticDiscountedProductPresenter,
)
from backend.frameworks_and_drivers.presenters.pydantic_presenters.retailer_presenter_and_schemas.presenter import (
    RetailerViewModel,
    RetailerResponse,
    PydanticRestRetailerPresenter,
)
from backend.interface_adapters.ports.presenters.base_presenter import BasePresenter


class PresentersContainer(containers.DeclarativeContainer):
    category_presenter: providers.Provider[BasePresenter[CategoryViewModel, CategoryResponse]] = providers.Factory(
        PydanticCategoryPresenter
    )
    retailer_presenter: providers.Provider[BasePresenter[RetailerViewModel, RetailerResponse]] = providers.Factory(
        PydanticRestRetailerPresenter
    )
    discounted_product_presenter: providers.Provider[
        BasePresenter[DiscountedProductViewModel, DiscountedProductResponse]
    ] = providers.Factory(PydanticDiscountedProductPresenter)
