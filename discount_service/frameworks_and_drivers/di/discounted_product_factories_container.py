from typing import AsyncIterator

from dependency_injector import providers, containers
from contextlib import asynccontextmanager

from discount_service.core.application.ports.patterns.discounted_product_factory import IDiscountedProductFactory
from discount_service.core.application.ports.repositories.entites_repositories.category import CategoryRepository
from discount_service.core.application.ports.repositories.entites_repositories.retailer import RetailerRepository
from discount_service.frameworks_and_drivers.patterns.factories.discounted_product import (
    YerevanCityDiscountedProductFactory,
)
import constants


@asynccontextmanager
async def create_yerevan_city_factory(
    retailer_repository: RetailerRepository,
    category_repository: CategoryRepository,
    yerevan_city_api_url: str,
    yerevan_city_discount_page_url: str,
) -> AsyncIterator[IDiscountedProductFactory]:
    retailer = await retailer_repository.get_by_name(constants.YEREVAN_CITY_RETAILER_NAME)
    try:
        yield YerevanCityDiscountedProductFactory(
            category_repository=category_repository,
            retailer_uuid=retailer.get_uuid(),
            yerevan_city_api_url=yerevan_city_api_url,
            yerevan_city_discount_page_url=yerevan_city_discount_page_url,
        )
    finally:
        pass


class DiscountedProductFactoriesContainer(containers.DeclarativeContainer):
    config: providers.Configuration = providers.Configuration()

    repositories_container: providers.DependenciesContainer = providers.DependenciesContainer()

    yerevan_city_discounted_product_factory: providers.Resource[IDiscountedProductFactory] = providers.Resource(
        create_yerevan_city_factory,
        retailer_repository=repositories_container.retailer_repository,
        category_repository=repositories_container.category_repository,
        yerevan_city_api_url=config.yerevan_city_api_url,
        yerevan_city_discount_page_url=config.yerevan_city_discount_page_url,
    )
