from constants import RetailersNames
from discount_service.core.application.patterns.discounted_products_collector_service_factory import (
    DiscountedProductsCollectorServiceCreator,
)
from discount_service.frameworks_and_drivers.di import get_service_container


async def get_discounted_product_collector_service_factory(
    retailer_name: str,
) -> DiscountedProductsCollectorServiceCreator:
    retailer_name_collector_service_map = {
        f"{RetailersNames.YEREVAN_CITY}": await get_service_container().discounted_products_collector_service_factories_container.container.yerevan_city_discounted_product_collector_service_factory.async_()
    }
    return retailer_name_collector_service_map[retailer_name]
