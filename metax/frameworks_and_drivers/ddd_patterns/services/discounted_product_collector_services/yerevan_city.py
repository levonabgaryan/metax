import asyncio
import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, AsyncIterator, override

import httpx

from metax.core.application.ports.ddd_patterns.service.discounted_product_collector_service import (
    DiscountedProductCollectorService,
)
from metax.core.domain.entities.discounted_product.entity import (
    DiscountedProduct,
)
from metax.core.domain.entities.discounted_product.value_objects import PriceDetails
from metax.core.domain.entities.retailer.entity import Retailer
from metax.core.domain.general_value_objects import EntityDateTimeDetails, UUIDValueObject
from metax.frameworks_and_drivers.ddd_patterns.services.discounted_product_collector_services.errors import (
    InvalidUrlForScrappingError,
)
from metax.frameworks_and_drivers.mixins.discounted_product_fields_cleaner import (
    DiscountedProductFieldsCleanerMixin,
)

logger = logging.getLogger(__name__)


class YerevanCityCollectorService(DiscountedProductCollectorService, DiscountedProductFieldsCleanerMixin):
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
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            try:
                response = await client.post(
                    url=self.__yerevan_city_data_source_url, json=self.__get_scrapper_payload()
                )
                response.raise_for_status()
            except httpx.InvalidURL as e:
                logger.error(e)
                raise InvalidUrlForScrappingError(invalid_url=self.__yerevan_city_data_source_url) from e
            except Exception as err:
                logger.error("Request to Yerevan city failed", err, exc_info=True)

        data = response.json()
        raw_products: list[dict[str, Any]] = data.get("data", {}).get("list", [])

        for raw_product in raw_products:
            yield DiscountedProduct(
                discounted_product_uuid=UUIDValueObject(uuid.uuid7()),
                name=self.clean_discounted_product_name(text=raw_product["name"]),
                price_details=PriceDetails(
                    real_price=Decimal(self.clean_discounted_product_price(raw_product["price"])),
                    discounted_price=Decimal(self.clean_discounted_product_price(raw_product["discountedPrice"])),
                ),
                url=f"{self.__yerevan_city_products_details_url}/{raw_product['id']}",
                datetime_details=EntityDateTimeDetails(
                    created_at=start_date_of_collecting,
                    updated_at=start_date_of_collecting,
                ),
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
