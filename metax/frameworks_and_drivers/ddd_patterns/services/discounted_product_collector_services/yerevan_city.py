import asyncio
import datetime as dt
import logging
import uuid
from collections.abc import AsyncIterator
from decimal import Decimal
from typing import Any, ClassVar, override

import httpx

from metax.core.application.ports.ddd_patterns.service.discounted_product_collector_service import (
    DiscountedProductCollectorService,
)
from metax.core.domain.entities.discounted_product.aggregate_root_entity import (
    DiscountedProduct,
)
from metax.core.domain.entities.retailer.aggregate_root_entity import Retailer
from metax.frameworks_and_drivers.ddd_patterns.services.discounted_product_collector_services.errors import (
    InvalidUrlForScrappingError,
)
from metax.frameworks_and_drivers.mixins.discounted_product_fields_cleaner import (
    DiscountedProductFieldsCleanerMixin,
)

logger = logging.getLogger(__name__)


class YerevanCityCollectorService(DiscountedProductCollectorService, DiscountedProductFieldsCleanerMixin):
    discounted_products_page_url: ClassVar[str] = "https://apishopv2.yerevan-city.am/api/Product/GetDiscounted"
    product_page_base_url: ClassVar[str] = "https://yerevan-city.am/shop/product-details"

    def __init__(
        self,
        retailer: Retailer,
    ) -> None:
        super().__init__(retailer=retailer)

    @override
    async def collect(self, start_date_of_collecting: dt.datetime) -> AsyncIterator[DiscountedProduct]:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            try:
                response = await client.post(
                    url=self.discounted_products_page_url, json=self.__get_scrapper_payload()
                )
                response.raise_for_status()
            except httpx.InvalidURL as e:
                logger.error(e)
                raise InvalidUrlForScrappingError(invalid_url=self.discounted_products_page_url) from e
            except Exception:
                logger.exception("Request to Yerevan city failed")

        data = response.json()
        raw_products: list[dict[str, Any]] = data.get("data", {}).get("list", [])

        for raw_product in raw_products:
            yield DiscountedProduct(
                uuid_=uuid.uuid7(),
                name=self.clean_discounted_product_name(text=raw_product["name"]),
                real_price=Decimal(self.clean_discounted_product_price(raw_product["price"])),
                discounted_price=Decimal(self.clean_discounted_product_price(raw_product["discountedPrice"])),
                url=f"{self.product_page_base_url}/{raw_product['id']}",
                created_at=start_date_of_collecting,
                updated_at=start_date_of_collecting,
                retailer_uuid=self._retailer.get_uuid(),
                category_uuid=None,
            )
            await asyncio.sleep(0.0)

    @staticmethod
    def __get_scrapper_payload() -> dict[str, Any]:
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
