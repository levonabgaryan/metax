from dependency_injector import containers, providers
from opensearchpy import AsyncOpenSearch

from discount_service.core.application.ports.repositories.entites_repositories.category import CategoryRepository
from discount_service.core.application.ports.repositories.entites_repositories.discounted_product import (
    DiscountedProductRepository,
)
from discount_service.core.application.ports.repositories.entites_repositories.retailer import RetailerRepository
from discount_service.core.application.ports.repositories.read_models_repositories.discounted_product_read_model import (
    IDiscountedProductReadModelRepository,
)
from discount_service.frameworks_and_drivers.repositories.opensearch.discounted_product_read_model import (
    OpenSearchDiscountedProductReadModelRepository,
)
from discount_service.frameworks_and_drivers.repositories.sql_lite.category import DjangoSqlLiteCategoryRepository
from discount_service.frameworks_and_drivers.repositories.sql_lite.discounted_product import (
    DjangoSqlLiteDiscountedProductRepository,
)
from discount_service.frameworks_and_drivers.repositories.sql_lite.retailer import DjangoSqlLiteRetailerRepository


class RepositoriesContainer(containers.DeclarativeContainer):
    opensearch_async_client: providers.Dependency[AsyncOpenSearch] = providers.Dependency(
        instance_of=AsyncOpenSearch
    )
    discounted_product_repository: providers.Provider[DiscountedProductRepository] = providers.Factory(
        DjangoSqlLiteDiscountedProductRepository
    )
    category_repository: providers.Provider[CategoryRepository] = providers.Factory(
        DjangoSqlLiteCategoryRepository
    )
    retailer_repository: providers.Provider[RetailerRepository] = providers.Factory(
        DjangoSqlLiteRetailerRepository
    )
    discounted_product_read_model_repository: providers.Provider[IDiscountedProductReadModelRepository] = (
        providers.Factory(
            OpenSearchDiscountedProductReadModelRepository,
            opensearch_async_client=opensearch_async_client,
        )
    )
