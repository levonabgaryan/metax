import asyncio
import datetime as dt
import logging
import uuid
from collections.abc import AsyncIterator
from decimal import Decimal
from json import loads
from urllib.parse import urljoin
from typing import ClassVar, override

import httpx
from bs4 import BeautifulSoup

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


class SasAmCollectorService(DiscountedProductCollectorService, DiscountedProductFieldsCleanerMixin):
    DATA_SOURCE_URL_LIMIT_PARAM: ClassVar[int] = 60
    MAX_PRODUCTS_COUNT: ClassVar[int] = 900

    sas_am_main_page_url: ClassVar[str] = "https://www.sas.am"
    product_link_base_url: ClassVar[str] = "https://www.sas.am/catalog/discount"

    def __init__(
        self,
        retailer: Retailer,
    ) -> None:
        super().__init__(retailer=retailer)

    @override
    async def collect(self, start_date_of_collecting: dt.datetime) -> AsyncIterator[DiscountedProduct]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for offset_param in range(0, self.MAX_PRODUCTS_COUNT, self.DATA_SOURCE_URL_LIMIT_PARAM):
                if offset_param == 0:
                    url_ = f"{self.product_link_base_url}/?LIMIT={self.DATA_SOURCE_URL_LIMIT_PARAM}"
                else:
                    url_ = f"{self.product_link_base_url}/?LIMIT={self.DATA_SOURCE_URL_LIMIT_PARAM}&offset={offset_param}"  # noqa: E501

                try:
                    response = await client.get(url=url_)
                    response.raise_for_status()
                except httpx.InvalidURL as err:
                    logger.error(err)
                    raise InvalidUrlForScrappingError(invalid_url=url_) from err
                except Exception as err:
                    logger.error("Request to SAS AM Failed", exc_info=err)
                    continue

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

                    raw_product_url = f"{self.sas_am_main_page_url}{href}" if href.startswith("/") else href

                    image_url: str | None = None
                    picture_tag = p_wrap.find("v-picture")
                    if picture_tag is not None:
                        sources_payload = picture_tag.get(":sources") or picture_tag.get("sources")
                        if isinstance(sources_payload, str) and sources_payload:
                            try:
                                sources = loads(sources_payload)
                            except ValueError:
                                sources = {}
                            for candidate_key in ("big_2x", "big", "middle_2x", "middle", "small_2x", "small"):
                                candidate_url = sources.get(candidate_key)
                                if isinstance(candidate_url, str) and candidate_url:
                                    image_url = urljoin(self.sas_am_main_page_url, candidate_url)
                                    break
                    if image_url is None:
                        img_tag = a_tag.find("img")
                        if img_tag is not None:
                            # Prefer data-src: lazy-loaded pages put the real URL there while src holds a placeholder.
                            src = img_tag.get("data-src") or img_tag.get("src")
                            if isinstance(src, str) and src and not src.startswith("data:"):
                                image_url = urljoin(self.sas_am_main_page_url, src)

                    yield DiscountedProduct(
                        uuid_=uuid.uuid7(),
                        name=self.clean_discounted_product_name(text=name),
                        real_price=Decimal(self.clean_discounted_product_price(old_span.text.strip())),
                        discounted_price=Decimal(self.clean_discounted_product_price(new_span.text.strip())),
                        url=raw_product_url,
                        image_url=image_url,
                        created_at=start_date_of_collecting,
                        updated_at=start_date_of_collecting,
                        retailer_uuid=self._retailer.get_uuid(),
                        category_uuid=None,
                    )
                    await asyncio.sleep(0.0)
