from opensearchpy import AsyncOpenSearch

from discount_service.core.application.ports.patterns.repositories_abstract_factory import (
    IRepositoriesAbstractFactory,
)
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


class RepositoriesAbstractFactory(IRepositoriesAbstractFactory):
    def __init__(self, opensearch_async_client: AsyncOpenSearch) -> None:
        self.opensearch_async_client = opensearch_async_client

    @staticmethod
    def create_discounted_product_repository() -> DiscountedProductRepository:
        return DjangoSqlLiteDiscountedProductRepository()

    @staticmethod
    def create_retailer_repository() -> RetailerRepository:
        return DjangoSqlLiteRetailerRepository()

    @staticmethod
    def create_category_repository() -> CategoryRepository:
        return DjangoSqlLiteCategoryRepository()

    def create_discounted_product_read_model_repository(self) -> IDiscountedProductReadModelRepository:
        return OpenSearchDiscountedProductReadModelRepository(
            opensearch_async_client=self.opensearch_async_client,
        )
