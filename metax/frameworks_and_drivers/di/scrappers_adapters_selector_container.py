from __future__ import annotations
from dependency_injector import providers, containers

from constants import RetailersNames

SCRAPPER_REGISTRY: dict[RetailersNames, str] = {
    RetailersNames.YEREVAN_CITY: "yerevan_city_scrapper_adapter",
    RetailersNames.SAS_AM: "sas_am_scrapper_adapter",
}


def get_scrapper_adapter_name(retailer_name: str) -> str:
    retailer_name = RetailersNames(retailer_name)
    return SCRAPPER_REGISTRY[retailer_name]


class ScrappersAdaptersSelectorContainer(containers.DeclarativeContainer):
    scrappers_adapters_container: providers.DependenciesContainer = providers.DependenciesContainer()

    scrapper_adapter = providers.FactoryAggregate(
        yerevan_city_scrapper_adapter=scrappers_adapters_container.yerevan_city_scrapper_adapter,
        sas_am_scrapper_adapter=scrappers_adapters_container.sas_am_scrapper_adapter,
    )
