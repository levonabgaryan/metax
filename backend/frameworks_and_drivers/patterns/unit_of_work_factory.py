from backend.core.application.patterns.unit_of_work_factory import IUnitOfWorkFactory
from backend.core.application.ports.patterns.unit_of_work import UnitOfWork
from backend.frameworks_and_drivers.patterns.unit_of_work import DjangoUnitOfWork
from backend.frameworks_and_drivers.repositories.category import DjangoSqlLiteCategoryRepository
from backend.frameworks_and_drivers.repositories.discounted_product import DjangoSqlLiteDiscountedProductRepository
from backend.frameworks_and_drivers.repositories.retailer import DjangoSqlLiteRetailerRepository


class DjangoUnitOfWorkFactory(IUnitOfWorkFactory):
    def create(self) -> UnitOfWork:
        return DjangoUnitOfWork(
            category_repository=DjangoSqlLiteCategoryRepository(),
            retailer_repository=DjangoSqlLiteRetailerRepository(),
            discounted_product_repository=DjangoSqlLiteDiscountedProductRepository(),
        )
