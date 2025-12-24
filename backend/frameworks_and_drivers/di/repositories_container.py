from dependency_injector import containers, providers

from backend.core.application.input_ports.repositories.category import CategoryRepository
from backend.core.application.input_ports.repositories.discounted_product import DiscountedProductRepository
from backend.core.application.input_ports.repositories.retailer import RetailerRepository
from backend.frameworks_and_drivers.repositories.category import DjangoSqlLiteCategoryRepository
from backend.frameworks_and_drivers.repositories.discounted_product import DjangoSqlLiteDiscountedProductRepository
from backend.frameworks_and_drivers.repositories.retailer import DjangoSqlLiteRetailerRepository


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
