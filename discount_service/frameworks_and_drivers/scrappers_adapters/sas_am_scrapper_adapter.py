import asyncio
import uuid
from datetime import datetime
from decimal import Decimal
from typing import AsyncIterator, ClassVar

import httpx
from bs4 import BeautifulSoup

from discount_service.core.domain.entities.discounted_product_entity.discounted_product import DiscountedProduct, \
    PriceDetails
from discount_service.core.domain.entities.retailer_entity.retailer import Retailer
from discount_service.frameworks_and_drivers.scrappers_adapters.scrapper_adapter import (
    ScrapperAdapter,
    DiscountedProductDTOFromYRetailer,
)


class SasAmScrapperAdapter(ScrapperAdapter):
    DATA_SOURCE_URL_LIMIT_PARAM: ClassVar[int] = 60
    MAX_PRODUCTS_COUNT: ClassVar[int] = 900

    def __init__(self, sas_am_data_source_url: str, sas_am_main_page_url: str) -> None:
        super().__init__(data_source_url=sas_am_data_source_url)
        self._sas_am_main_page_url = sas_am_main_page_url

    async def fetch(self, started_time: datetime, retailer: Retailer) -> AsyncIterator[DiscountedProduct]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for offset_param in range(0, self.MAX_PRODUCTS_COUNT, self.DATA_SOURCE_URL_LIMIT_PARAM):
                if offset_param == 0:
                    url_ = f"{self._data_source_url}/?LIMIT={self.DATA_SOURCE_URL_LIMIT_PARAM}"
                else:
                    url_ = (
                        f"{self._data_source_url}/?LIMIT={self.DATA_SOURCE_URL_LIMIT_PARAM}&offset={offset_param}"
                    )

                response = await client.get(url=url_)
                soup = BeautifulSoup(response.text, "lxml")

                items_block_divs = soup.find("div", class_="catalog__grid grid")
                if items_block_divs is None:
                    continue

                products_div = items_block_divs.find_all(
                    "div", class_="catalog__col col-xl-3 col-lg-3 col-md-4 col-sm-6 col-xs-12"
                )

                for product_div in products_div:
                    p_wrap = product_div.find(
                        "div", class_="product js-product js-hover-dropdown-bk product--web-catalog"
                    )
                    if p_wrap is None:
                        continue

                    name_tag = p_wrap.find("div", class_="product__name hidden-sm")
                    if name_tag is None:
                        continue
                    name = name_tag.text.strip()

                    price_container = product_div.find("div", class_="product__price price")
                    if price_container is None:
                        continue

                    old_price_block = price_container.find("div", class_="price__old")
                    new_price_block = price_container.find("div", class_="price__new")

                    if old_price_block is None or new_price_block is None:
                        continue

                    old_span = old_price_block.find("span", class_="price__text")
                    new_span = new_price_block.find("span", class_="price__text")

                    if old_span is None or new_span is None:
                        continue

                    a_tag = product_div.find("a", class_="product__cover-link")
                    if a_tag is None:
                        continue

                    href = a_tag.get("href")
                    if not isinstance(href, str):
                        continue

                    raw_product_url = f"{self._sas_am_main_page_url}{href}" if href.startswith("/") else href

                    yield DiscountedProduct(
                        discounted_product_uuid=uuid.uuid4(),
                        name=self._clean_discounted_product_name(text=name),
                        price_details=PriceDetails(
                            real_price=Decimal(self._clean_discounted_product_price(old_span.text.strip())),
                            discounted_price=Decimal(self._clean_discounted_product_price(new_span.text.strip())),
                        ),
                        url=raw_product_url,
                        created_at=started_time,
                        retailer_uuid=retailer.get_uuid(),
                        category_uuid=None
                    )
                    await asyncio.sleep(0.1)
