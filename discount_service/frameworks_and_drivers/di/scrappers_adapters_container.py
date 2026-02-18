from dependency_injector import providers, containers

from discount_service.frameworks_and_drivers.scrappers.scrapper_abc import ScrapperAdapter
from discount_service.frameworks_and_drivers.scrappers.yerevan_city_scrapper import (
    YerevanCityScrapperAdapter,
    DiscountedProductDTOFromYerevanCityScrapper,
)


class ScrappersAdaptersContainer(containers.DeclarativeContainer):
    config: providers.Configuration = providers.Configuration()

    yerevan_city_scrapper_adapter: providers.Provider[
        ScrapperAdapter[DiscountedProductDTOFromYerevanCityScrapper]
    ] = providers.ThreadSafeSingleton(
        YerevanCityScrapperAdapter,
        yerevan_city_data_source_url=config.yerevan_city_data_source_url,
        yerevan_city_products_details_url=config.yerevan_city_products_details_url,
    )
