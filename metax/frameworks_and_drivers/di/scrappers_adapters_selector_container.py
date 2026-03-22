from __future__ import annotations

from constants import RetailersNames
from metax.core.application.patterns.strategies.discounted_product.discounted_product_collector_strategy import (
    DiscountedProductCollectorStrategy,
)
from metax.frameworks_and_drivers.patterns.strategies.discounted_product.sas_am_strategy import SasAmStrategy
from metax.frameworks_and_drivers.patterns.strategies.discounted_product.yerevan_city_strategy import (
    YerevanCityStrategy,
)

RETAILER_NAME_DISCOUNTED_PRODUCT_COLLECTOR_STRATEGY: dict[
    RetailersNames, type[DiscountedProductCollectorStrategy]
] = {
    RetailersNames.YEREVAN_CITY: YerevanCityStrategy,
    RetailersNames.SAS_AM: SasAmStrategy,
}
