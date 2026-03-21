from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import Configuration

from metax.frameworks_and_drivers.scrappers_adapters.scrapper_adapter import ScrapperAdapter
from metax.frameworks_and_drivers.scrappers_adapters.yerevan_city_scrapper_adapter import (
    YerevanCityScrapperAdapter,
)


class ScrappersAdaptersContainer(DeclarativeContainer):
    config: providers.Configuration = Configuration()

    yerevan_city_scrapper_adapter: providers.Factory[ScrapperAdapter] = providers.Factory(
        YerevanCityScrapperAdapter,
        yerevan_city_data_source_url=config.yerevan_city_data_source_url,
        yerevan_city_products_details_url=config.yerevan_city_products_details_url,
    )
