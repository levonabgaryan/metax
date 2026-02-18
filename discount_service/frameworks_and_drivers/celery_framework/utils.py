from constants import RetailersNames
from discount_service.core.application.ports.patterns.factories.discounted_products_collector_service_factory import (
    DiscountedProductsCollectorServiceCreator,
)
from discount_service.frameworks_and_drivers.di import get_service_container


async def get_discounted_product_collector_service_factory(
    retailer_name: str,
) -> DiscountedProductsCollectorServiceCreator:
    retailer_name_collector_service_map = {
        f"{RetailersNames.YEREVAN_CITY}": await get_service_container().patterns_container.container.yerevan_city_discounted_products_collector_service_factory.async_()
    }
    return retailer_name_collector_service_map[retailer_name]
