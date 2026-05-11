from dependency_injector import containers, providers

from metax.core.application.ports.ddd_patterns.repository.entites_repositories.category import CategoryRepository
from metax.core.application.ports.ddd_patterns.repository.entites_repositories.discounted_product import (
    DiscountedProductRepository,
)
from metax.core.application.ports.ddd_patterns.repository.entites_repositories.retailer import RetailerRepository
from metax.core.application.ports.ddd_patterns.repository.read_models_repositories.discounted_product_read_model import (  # noqa: E501
    DiscountedProductReadModelRepository,
)
from metax.frameworks_and_drivers.ddd_patterns.repositories.opensearch.discounted_product_read_model import (
    OpenSearchDiscountedProductReadModelRepository,
)
from metax.frameworks_and_drivers.ddd_patterns.repositories.postgres.category import (
    DjangoPostgresqlCategoryRepository,
)
from metax.frameworks_and_drivers.ddd_patterns.repositories.postgres.discounted_product import (
    DjangoPostgresqlDiscountedProductRepository,
)
from metax.frameworks_and_drivers.ddd_patterns.repositories.postgres.retailer import (
    DjangoPostgresqlRetailerRepository,
)


class RepositoriesContainer(containers.DeclarativeContainer):
    resources_container: providers.DependenciesContainer = providers.DependenciesContainer()

    discounted_product_repository: providers.Provider[DiscountedProductRepository] = providers.Factory(
        DjangoPostgresqlDiscountedProductRepository
    )
    category_repository: providers.Provider[CategoryRepository] = providers.Factory(
        DjangoPostgresqlCategoryRepository
    )
    retailer_repository: providers.Provider[RetailerRepository] = providers.Factory(
        DjangoPostgresqlRetailerRepository
    )
    discounted_product_read_model_repository: providers.Provider[DiscountedProductReadModelRepository] = (
        providers.Factory(
            OpenSearchDiscountedProductReadModelRepository,
            opensearch_async_client=resources_container.opensearch_async_client,
        )
    )
