from dependency_injector import containers, providers

from discount_service.core.application.patterns.use_case_abc import UseCase
from discount_service.core.application.use_cases.discounted_product.collect_discounted_products_from_retailer import (
    CollectDiscountedProductsFromRetailer,
)
from discount_service.core.application.use_cases.discounted_product.dtos import (
    CollectDiscountedProductsFromRetailerRequest,
    CollectDiscountedProductsFromRetailerResponse,
)


class DiscountedProductUseCasesContainer(containers.DeclarativeContainer):
    patterns_container: providers.DependenciesContainer = providers.DependenciesContainer()

    collect_discounted_products_from_retailer: providers.Provider[
        UseCase[CollectDiscountedProductsFromRetailerRequest, CollectDiscountedProductsFromRetailerResponse]
    ] = providers.Factory(
        CollectDiscountedProductsFromRetailer,
        unit_of_work=patterns_container.unit_of_work,
        discounted_product_factory=patterns_container.discounted_product_factory,
    )


class UseCasesContainer(containers.DeclarativeContainer):
    patterns_container = providers.DependenciesContainer()

    discounted_product = providers.Container(
        DiscountedProductUseCasesContainer, patterns_container=patterns_container
    )
