from dependency_injector import containers, providers

from backend.frameworks_and_drivers.presenters.pydantic_presenters.category_presenter_and_schemas.presenter import (
    CategoryViewModel,
    CategoryResponseDTO,
    PydanticCategoryPresenter,
)
from backend.frameworks_and_drivers.presenters.pydantic_presenters.discounted_product_presenter_and_schemas.presenter import (
    DiscountedProductViewModel,
    DiscountedProductResponseDTO,
    PydanticDiscountedProductPresenter,
)
from backend.frameworks_and_drivers.presenters.pydantic_presenters.retailer_presenter_and_schemas.presenter import (
    RetailerViewModel,
    RetailerResponseDTO,
    PydanticRestRetailerPresenter,
)
from backend.interface_adapters.ports.presenters.base_presenter import BasePresenter


class PresentersContainer(containers.DeclarativeContainer):
    category_presenter: providers.Provider[BasePresenter[CategoryResponseDTO, CategoryViewModel]] = (
        providers.Factory(PydanticCategoryPresenter)
    )
    retailer_presenter: providers.Provider[BasePresenter[RetailerResponseDTO, RetailerViewModel]] = (
        providers.Factory(PydanticRestRetailerPresenter)
    )
    discounted_product_presenter: providers.Provider[
        BasePresenter[DiscountedProductResponseDTO, DiscountedProductViewModel]
    ] = providers.Factory(PydanticDiscountedProductPresenter)
