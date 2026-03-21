from dependency_injector import containers, providers
from opensearchpy import AsyncOpenSearch

from metax.core.application.ports.repositories.entites_repositories.category import CategoryRepository
from metax.core.application.ports.repositories.entites_repositories.discounted_product import (
    DiscountedProductRepository,
)
from metax.core.application.ports.repositories.entites_repositories.retailer import RetailerRepository
from metax.core.application.ports.repositories.read_models_repositories.discounted_product_read_model import (
    IDiscountedProductReadModelRepository,
)
from metax.frameworks_and_drivers.repositories.opensearch.discounted_product_read_model import (
    OpenSearchDiscountedProductReadModelRepository,
)
from metax.frameworks_and_drivers.repositories.postgres.category import (
    DjangoPostgresqlCategoryRepository,
)
from metax.frameworks_and_drivers.repositories.postgres.discounted_product import (
    DjangoPostgresqlDiscountedProductRepository,
)
from metax.frameworks_and_drivers.repositories.postgres.retailer import (
    DjangoPostgresqlRetailerRepository,
)


class RepositoriesContainer(containers.DeclarativeContainer):
    opensearch_async_client: providers.Dependency[AsyncOpenSearch] = providers.Dependency(
        instance_of=AsyncOpenSearch
    )
    discounted_product_repository: providers.Provider[DiscountedProductRepository] = providers.Factory(
        DjangoPostgresqlDiscountedProductRepository
    )
    category_repository: providers.Provider[CategoryRepository] = providers.Factory(
        DjangoPostgresqlCategoryRepository
    )
    retailer_repository: providers.Provider[RetailerRepository] = providers.Factory(
        DjangoPostgresqlRetailerRepository
    )
    discounted_product_read_model_repository: providers.Provider[IDiscountedProductReadModelRepository] = (
        providers.Factory(
            OpenSearchDiscountedProductReadModelRepository,
            opensearch_async_client=opensearch_async_client,
        )
    )
