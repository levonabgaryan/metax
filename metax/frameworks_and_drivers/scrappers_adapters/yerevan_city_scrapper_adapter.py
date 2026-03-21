import asyncio
import uuid
from datetime import datetime
from typing import Any, AsyncIterator, override

import httpx

from metax.core.domain.entities.discounted_product_entity.discounted_product import (
    DiscountedProduct,
)
from metax.core.domain.entities.retailer_entity.retailer import Retailer
from metax.frameworks_and_drivers.scrappers_adapters.scrapper_adapter import (
    ScrapperAdapter,
)


class YerevanCityScrapperAdapter(ScrapperAdapter):
    def __init__(self, yerevan_city_data_source_url: str, yerevan_city_products_details_url: str):
        super().__init__(data_source_url=yerevan_city_data_source_url)
        self._yerevan_city_products_details_url = yerevan_city_products_details_url

    @override
    async def fetch(self, started_time: datetime, retailer: Retailer) -> AsyncIterator[DiscountedProduct]:
        async with httpx.AsyncClient(timeout=25) as client:
            try:
                response = await client.post(url=self._data_source_url, json=self.get_scrapper_payload())
                response.raise_for_status()
            except Exception as e:
                print(e.args[0])
                return

        data = response.json()
        raw_products: list[dict[str, Any]] = data.get("data", {}).get("list", [])

        for raw_product in raw_products:
            yield self._create_discounted_product(
                discounted_product_uuid=uuid.uuid4(),
                retailer_uuid=retailer.get_uuid(),
                real_price=str(raw_product["price"]),
                discounted_price=str(raw_product["discounted_price"]),
                name=raw_product["name"],
                created_at=started_time,
                url=f"{self._yerevan_city_products_details_url}/{raw_product['id']}",
            )
            await asyncio.sleep(0)

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
