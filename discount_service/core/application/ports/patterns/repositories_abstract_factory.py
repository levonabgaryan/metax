from abc import ABC, abstractmethod

from discount_service.core.application.ports.repositories.entites_repositories.category import CategoryRepository
from discount_service.core.application.ports.repositories.entites_repositories.discounted_product import (
    DiscountedProductRepository,
)
from discount_service.core.application.ports.repositories.entites_repositories.retailer import RetailerRepository
from discount_service.core.application.ports.repositories.read_models_repositories.discounted_product_read_model import (
    IDiscountedProductReadModelRepository,
)


class IRepositoriesAbstractFactory(ABC):
    @staticmethod
    @abstractmethod
    def create_discounted_product_repository() -> DiscountedProductRepository:
        pass

    @staticmethod
    @abstractmethod
    def create_retailer_repository() -> RetailerRepository:
        pass

    @staticmethod
    @abstractmethod
    def create_category_repository() -> CategoryRepository:
        pass

    @abstractmethod
    def create_discounted_product_read_model_repository(self) -> IDiscountedProductReadModelRepository:
        pass
