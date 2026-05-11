import datetime as dt
from typing import override

from metax.core.application.ports.design_patterns.factory.discounted_product_collector_service_creator import (
    DiscountedProductCollectorServiceCreator,
)
from metax.core.domain.entities.retailer.aggregate_root_entity import Retailer
from metax.frameworks_and_drivers.ddd_patterns.services.discounted_product_collector_services.sas_am import (
    SasAmCollectorService,
)
from metax.frameworks_and_drivers.ddd_patterns.services.discounted_product_collector_services.yerevan_city import (
    YerevanCityCollectorService,
)


class YerevanCityDiscountProductCollectorCreator(DiscountedProductCollectorServiceCreator):
    def __init__(
        self,
        start_date_of_collecting: dt.datetime,
        retailer: Retailer,
    ) -> None:
        super().__init__(start_date_of_collecting=start_date_of_collecting)
        self.__retailer = retailer

    @override
    def create_collector_service(self) -> YerevanCityCollectorService:
        return YerevanCityCollectorService(
            retailer=self.__retailer,
        )


class SasAmDiscountProductCollectorCreator(DiscountedProductCollectorServiceCreator):
    def __init__(
        self,
        start_date_of_collecting: dt.datetime,
        retailer: Retailer,
    ) -> None:
        super().__init__(start_date_of_collecting=start_date_of_collecting)
        self.__retailer = retailer

    @override
    def create_collector_service(self) -> SasAmCollectorService:
        return SasAmCollectorService(
            retailer=self.__retailer,
        )
