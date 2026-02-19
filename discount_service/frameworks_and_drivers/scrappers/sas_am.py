import asyncio
from typing import AsyncIterator

import httpx
from bs4 import BeautifulSoup

from discount_service.frameworks_and_drivers.scrappers.scrapper_abc import (
    ScrapperAdapter,
    DiscountedProductDTOFromYRetailer,
)


class SasAmScrapperAdapter(ScrapperAdapter):
    def __init__(self, sas_am_data_source_url: str) -> None:
        super().__init__(data_source_url=sas_am_data_source_url)
        self.__data_source_url_offset = 60
        self.__data_source_url_offset_max_count = 900

    async def fetch(self) -> AsyncIterator[DiscountedProductDTOFromYRetailer]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for offset_param in range(0, self.__data_source_url_offset_max_count, self.__data_source_url_offset):
                if offset_param == 0:
                    url_ = f"{self._data_source_url}/?LIMIT=60"
                else:
                    url_ = f"{self._data_source_url}/?LIMIT=60&offset={offset_param}"

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

                    raw_product_url = f"https://www.sas.am{href}" if href.startswith("/") else href

                    yield DiscountedProductDTOFromYRetailer(
                        name=self._clean_discounted_product_name(text=name),
                        real_price=self._clean_discounted_product_price(old_span.text.strip()),
                        discounted_price=self._clean_discounted_product_price(new_span.text.strip()),
                        url=raw_product_url,
                    )
                    await asyncio.sleep(0.1)
