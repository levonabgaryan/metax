from __future__ import annotations
from dependency_injector import providers, containers

from constants import RetailersNames


SCRAPPER_REGISTRY: dict[RetailersNames, str] = {
    RetailersNames.YEREVAN_CITY: "yerevan_city_scrapper_adapter",
    RetailersNames.SAS_AM: "sas_am_scrapper_adapter",
}

class ScrappersAdaptersSelectorContainer(containers.DeclarativeContainer):
    scrappers_adapters_container: providers.DependenciesContainer = providers.DependenciesContainer()

    retailer_name: providers.Dependency[str] = providers.Dependency()

    selector_key = providers.Callable(
        lambda r: SCRAPPER_REGISTRY[r],
        retailer_name,
    )

    scrapper_adapter = providers.Selector(
        selector_key,
        yerevan_city_scrapper_adapter=scrappers_adapters_container.yerevan_city_scrapper_adapter,
        sas_am_scrapper_adapter=scrappers_adapters_container.sas_am_scrapper_adapter,
    )
