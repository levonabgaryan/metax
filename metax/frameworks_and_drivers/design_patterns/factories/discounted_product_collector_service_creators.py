from datetime import datetime
from typing import override

from metax.core.application.ports.design_patterns.factory.discounted_product_collector_service_creator import (
    DiscountedProductCollectorServiceCreator,
)
from metax.core.domain.entities.retailer.entity import Retailer
from metax.frameworks_and_drivers.ddd_patterns.services.discounted_product_collector_services.sas_am import (
    SasAmCollectorService,
)
from metax.frameworks_and_drivers.ddd_patterns.services.discounted_product_collector_services.yerevan_city import (
    YerevanCityCollectorService,
)


class YerevanCityDiscountProductCollectorCreator(DiscountedProductCollectorServiceCreator):
    def __init__(
        self,
        start_date_of_collecting: datetime,
        retailer: Retailer,
        yerevan_city_data_source_url: str,
        yerevan_city_products_details_url: str,
    ) -> None:
        super().__init__(start_date_of_collecting=start_date_of_collecting)
        self.__retailer = retailer
        self.__yerevan_city_data_source_url = yerevan_city_data_source_url
        self.__yerevan_city_products_details_url = yerevan_city_products_details_url

    @override
    def create_collector_service(self) -> YerevanCityCollectorService:
        return YerevanCityCollectorService(
            yerevan_city_data_source_url=self.__yerevan_city_data_source_url,
            yerevan_city_products_details_url=self.__yerevan_city_products_details_url,
            retailer=self.__retailer,
        )


class SasAmDiscountProductCollectorCreator(DiscountedProductCollectorServiceCreator):
    def __init__(
        self,
        start_date_of_collecting: datetime,
        retailer: Retailer,
        sas_am_data_source_url: str,
        sas_am_main_page_url: str,
    ) -> None:
        super().__init__(start_date_of_collecting=start_date_of_collecting)
        self.__retailer = retailer
        self.__sas_am_data_source_url = sas_am_data_source_url
        self.__sas_am_main_page_url = sas_am_main_page_url

    @override
    def create_collector_service(self) -> SasAmCollectorService:
        return SasAmCollectorService(
            sas_am_data_source_url=self.__sas_am_data_source_url,
            sas_am_main_page_url=self.__sas_am_main_page_url,
            retailer=self.__retailer,
        )
