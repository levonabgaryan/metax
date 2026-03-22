import asyncio
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, AsyncIterator, override

import httpx

from metax.core.application.patterns.strategies.discounted_product.discounted_product_collector_strategy import (
    DiscountedProductCollectorStrategy,
)
from metax.core.domain.entities.discounted_product.entity import (
    DiscountedProduct,
)
from metax.core.domain.entities.discounted_product.value_objects import PriceDetails
from metax.core.domain.entities.retailer.entity import Retailer
from metax.frameworks_and_drivers.mixins.discounted_product_fields_cleaner import (
    DiscountedProductFieldsCleanerMixin,
)


class YerevanCityStrategy(DiscountedProductCollectorStrategy, DiscountedProductFieldsCleanerMixin):
    def __init__(
        self,
        yerevan_city_data_source_url: str,
        yerevan_city_products_details_url: str,
        retailer: Retailer,
    ) -> None:
        super().__init__(retailer=retailer)
        self.__yerevan_city_data_source_url = yerevan_city_data_source_url
        self.__yerevan_city_products_details_url = yerevan_city_products_details_url

    @override
    async def collect(self, start_date_of_collecting: datetime) -> AsyncIterator[DiscountedProduct]:
        async with httpx.AsyncClient(timeout=25) as client:
            try:
                response = await client.post(
                    url=self.__yerevan_city_data_source_url, json=self.get_scrapper_payload()
                )
                response.raise_for_status()
            except Exception as e:
                print(e.args[0])
                return

        data = response.json()
        raw_products: list[dict[str, Any]] = data.get("data", {}).get("list", [])

        for raw_product in raw_products:
            yield DiscountedProduct(
                discounted_product_uuid=uuid.uuid4(),
                name=self.clean_discounted_product_name(text=raw_product["name"]),
                price_details=PriceDetails(
                    real_price=Decimal(self.clean_discounted_product_price(raw_product["price"])),
                    discounted_price=Decimal(self.clean_discounted_product_price(raw_product["discounted_price"])),
                ),
                url=f"{self.__yerevan_city_products_details_url}/{raw_product['id']}",
                created_at=start_date_of_collecting,
                retailer_uuid=self._retailer.get_uuid(),
                category_uuid=None,
            )
            await asyncio.sleep(0.0)

    @staticmethod
    def get_scrapper_payload() -> dict[str, Any]:
        return {
            "count": 10000,
            "page": 1,
            "priceFrom": 50,
            "priceTo": 545000,
            "countries": [],
            "categories": [],
            "brands": [],
            "search": None,
            "isDiscounted": True,
            "sortBy": 3,
            "type": 1,
        }
