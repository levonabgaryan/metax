from dependency_injector import containers, providers

from backend.core.application.patterns.use_case_abc import UseCase, EmptyResponseDTO
from backend.core.application.use_cases.category.add_new_category_helper_words import AddHelperWordsUseCase
from backend.core.application.use_cases.category.delete_helper_words import DeleteHelperWordsUseCase
from backend.core.application.use_cases.category.dtos import AddHelperWordsRequest, DeleteHelperWordsRequest
from backend.core.application.use_cases.discounted_product.collect_discounted_products_from_retailer import (
    CollectDiscountedProductsFromRetailerUseCase,
)
from backend.core.application.use_cases.discounted_product.dtos import CollectDiscountedProductsFromRetailerRequest
from backend.frameworks_and_drivers.di.patterns_container import PatternsContainer


class CategoryUseCaseContainer(containers.DeclarativeContainer):
    patterns: providers.Container[PatternsContainer] = providers.Container(PatternsContainer)

    add_new_helper_words: providers.Provider[UseCase[AddHelperWordsRequest, EmptyResponseDTO]] = providers.Factory(
        AddHelperWordsUseCase,
        unit_of_work=patterns.container.unit_of_work,
    )

    delete_helper_words: providers.Provider[UseCase[DeleteHelperWordsRequest, EmptyResponseDTO]] = (
        providers.Factory(
            DeleteHelperWordsUseCase,
            unit_of_work=patterns.container.unit_of_work,
        )
    )


class DiscountedProductUseCaseContainer(containers.DeclarativeContainer):
    patterns: providers.Container[PatternsContainer] = providers.Container(PatternsContainer)

    collect_discounted_products_from_retailer: providers.Provider[
        UseCase[CollectDiscountedProductsFromRetailerRequest, EmptyResponseDTO]
    ] = providers.Factory(
        CollectDiscountedProductsFromRetailerUseCase,
        unit_of_work=patterns.container.unit_of_work,
        discounted_product_factory=patterns.container.discounted_product_factory,
    )
