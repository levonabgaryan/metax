from dependency_injector import containers, providers

from discount_service.core.application.ports.repositories.category import CategoryRepository
from discount_service.core.application.ports.repositories.discounted_product import DiscountedProductRepository
from discount_service.core.application.ports.repositories.discounted_product_read_model import (
    DiscountedProductReadModelRepository,
)
from discount_service.core.application.ports.repositories.retailer import RetailerRepository
from discount_service.frameworks_and_drivers.repositories.category import DjangoSqlLiteCategoryRepository
from discount_service.frameworks_and_drivers.repositories.discounted_product import (
    DjangoSqlLiteDiscountedProductRepository,
)
from discount_service.frameworks_and_drivers.repositories.discounted_product_read_model import (
    DjangoSqlLiteDiscountedProductReadModelRepository,
)
from discount_service.frameworks_and_drivers.repositories.retailer import DjangoSqlLiteRetailerRepository


class RepositoriesContainer(containers.DeclarativeContainer):
    category_repository: providers.Provider[CategoryRepository] = providers.Factory(
        DjangoSqlLiteCategoryRepository
    )
    retailer_repository: providers.Provider[RetailerRepository] = providers.Factory(
        DjangoSqlLiteRetailerRepository
    )
    discounted_product_repository: providers.Provider[DiscountedProductRepository] = providers.Factory(
        DjangoSqlLiteDiscountedProductRepository
    )
    discounted_product_read_model_repository: providers.Provider[DiscountedProductReadModelRepository] = (
        providers.Factory(DjangoSqlLiteDiscountedProductReadModelRepository)
    )
