import asyncio
import uuid
from datetime import datetime
from typing import AsyncIterator, Any

import httpx

import constants
from discount_service.core.application.ports.patterns.discounted_product_factory import DiscountedProductFactory
from discount_service.core.application.ports.repositories.entites_repositories.category import CategoryRepository
from discount_service.core.application.ports.repositories.entites_repositories.retailer import RetailerRepository
from discount_service.core.application.ports.repositories.errors.errors import EntityIsNotFoundError
from discount_service.core.domain.entities.category_entity.category import Category
from discount_service.core.domain.entities.discounted_product_entity.discounted_product import (
    DiscountedProduct,
    PriceDetails,
)
from discount_service.core.domain.entities.retailer_entity.retailer import Retailer


class YerevanCityDiscountedProductFactory(DiscountedProductFactory):
    def __init__(
        self,
        category_repository: CategoryRepository,
        retailer_repository: RetailerRepository,
        yerevan_city_api_url: str,
        yerevan_city_discount_page_url: str,
    ) -> None:
        self.__retailer_discounted_products_api_url = yerevan_city_api_url
        self.__category_repository = category_repository
        self.__retailer_repository = retailer_repository
        self.__retailer: Retailer | None = None
        self.__yerevan_city_discount_page_url = yerevan_city_discount_page_url

    async def create_many_from_retailer(
        self, started_time: datetime, batch_size: int = 500
    ) -> AsyncIterator[list[DiscountedProduct]]:
        async with httpx.AsyncClient(timeout=25) as client:
            try:
                response = await client.post(
                    url=self.__retailer_discounted_products_api_url, json=self.get_scrapper_payload()
                )
            except Exception as e:
                print(e.args[0])
                yield []
                return

            discounted_products_from_retailer = response.json()["data"]["list"]

        batch: list[dict[str, Any]] = []
        for discounted_product in discounted_products_from_retailer:
            batch.append(discounted_product)

            if len(batch) >= batch_size:
                mapped_products = list(
                    await asyncio.gather(*[self.__map_to_entity(p, started_time) for p in batch])
                )
                yield mapped_products
                batch = []

        if batch:
            mapped_products = list(await asyncio.gather(*[self.__map_to_entity(p, started_time) for p in batch]))
            yield mapped_products

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

    async def __map_to_entity(
        self, discounted_product_from_retailer: dict[str, Any], created_at: datetime
    ) -> DiscountedProduct:
        if self.__retailer is None:
            self.__retailer = await self.__retailer_repository.get_by_name(constants.YEREVAN_CITY_RETAILER_NAME)
        category: Category | None
        words = self.clean_text_and_split(text=discounted_product_from_retailer["name"])
        try:
            category = await self.__category_repository.get_by_helper_words_in_words(words=words)
        except EntityIsNotFoundError as e:
            category = None
            print(e.args[0])

        id_from_retailer = discounted_product_from_retailer["id"]
        return DiscountedProduct(
            discounted_product_uuid=uuid.uuid4(),
            name=discounted_product_from_retailer["name"],
            price_details=PriceDetails(
                real_price=discounted_product_from_retailer["price"],
                discounted_price=discounted_product_from_retailer["discountedPrice"],
            ),
            category_uuid=category.get_uuid() if category is not None else None,
            retailer_uuid=self.__retailer.get_uuid(),
            created_at=created_at,
            url=f"{self.__yerevan_city_discount_page_url}/{id_from_retailer}",
        )
