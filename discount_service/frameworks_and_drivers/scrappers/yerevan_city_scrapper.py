import asyncio
import re
from typing import Any, AsyncIterator

import httpx

from discount_service.frameworks_and_drivers.scrappers.scrapper_abc import ScrapperAdapter, ScrapperBaseDTO


class DiscountedProductDTOFromYerevanCityScrapper(ScrapperBaseDTO):
    name: str
    real_price: str
    discounted_price: str
    url: str


class YerevanCityScrapperAdapter(ScrapperAdapter[DiscountedProductDTOFromYerevanCityScrapper]):
    def __init__(self, yerevan_city_data_source_url: str, yerevan_city_products_details_url: str):
        super().__init__(data_source_url=yerevan_city_data_source_url)
        self._yerevan_city_products_details_url = yerevan_city_products_details_url

    async def fetch(self) -> AsyncIterator[DiscountedProductDTOFromYerevanCityScrapper]:
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
            yield DiscountedProductDTOFromYerevanCityScrapper(
                name=self._clean_discounted_product_name(raw_product["name"]),
                real_price=str(raw_product["price"]),
                discounted_price=str(raw_product["discountedPrice"]),
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

    @staticmethod
    def _clean_discounted_product_name(text: str) -> str:
        """
        Normalize product name:
        - lowercase
        - remove special symbols
        - keep latin, cyrillic, armenian letters and digits
        - normalize spaces
        """
        text = text.lower()
        text = re.sub(
            r"[^a-z0-9а-яёա-ֆ]+",
            " ",
            text,
            flags=re.IGNORECASE,
        )
        # remove extra spaces
        text = re.sub(r"\s+", " ", text).strip()
        return text
