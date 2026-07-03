import asyncio
import datetime as dt
import logging
import uuid
from collections.abc import AsyncIterator
from decimal import Decimal
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


class TntesakanAmCollectorService(DiscountedProductCollectorService, DiscountedProductFieldsCleanerMixin):
    """Scrapes the single server-rendered discount page at ``/hy/discount``.

    The page lists every discounted product at once (no pagination). Each card carries two price
    spans (``span.sale`` and ``span.price``), the product name (``h6``), a link and an image. Which
    span holds the original vs. the sale price is *not* consistent across cards (some are swapped),
    so we take the higher of the two as the real price and the lower as the discounted price. A few
    cards carry a ``0 Դր`` placeholder for the missing original price — those are skipped, as are
    out-of-stock cards (which add a ``span.text-danger`` "Ապրանքը հասանելի չէ" badge), so we only
    surface products a user can actually buy at a real discount.

    Category is not set here — tntesakan.am is configured with a fixed ``default_category`` on the
    retailer, which the collection use case stamps onto every product (see CollectDiscountedProducts).
    """

    discounted_products_page_url: ClassVar[str] = "https://tntesakan.am/hy/discount"

    def __init__(
        self,
        retailer: Retailer,
    ) -> None:
        super().__init__(retailer=retailer)

    @override
    async def collect(self, start_date_of_collecting: dt.datetime) -> AsyncIterator[DiscountedProduct]:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0), follow_redirects=True) as client:
            try:
                response = await client.get(
                    url=self.discounted_products_page_url,
                    headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
                )
                response.raise_for_status()
            except httpx.InvalidURL as err:
                logger.error(err)
                raise InvalidUrlForScrappingError(invalid_url=self.discounted_products_page_url) from err
            except Exception:
                logger.exception("Request to tntesakan.am failed")
                return

        soup = BeautifulSoup(response.text, "lxml")
        product_boxes = soup.find_all("div", class_="productBox")

        for product_box in product_boxes:
            # Out-of-stock items carry a "Ապրանքը հասանելի չէ" badge; skip — the user can't buy them.
            if product_box.find("span", class_="text-danger") is not None:
                continue

            name_tag = product_box.find("h6")
            if name_tag is None:
                continue
            name = name_tag.get_text(strip=True)
            if not name:
                continue

            price_container = product_box.find("div", class_="productPrice")
            if price_container is None:
                continue
            sale_span = price_container.find("span", class_="sale")
            price_span = price_container.find("span", class_="price")
            if sale_span is None or price_span is None:
                continue
            # The two spans are not reliably ordered (original vs. sale), so derive real/discounted
            # by magnitude. A "0 Դր" placeholder (missing original) collapses the lower price to 0 —
            # skip those, we can't state a real discount for them.
            first_price = Decimal(self.clean_discounted_product_price(sale_span.text.strip()))
            second_price = Decimal(self.clean_discounted_product_price(price_span.text.strip()))
            real_price = max(first_price, second_price)
            discounted_price = min(first_price, second_price)
            if discounted_price <= 0:
                continue

            link_tag = product_box.find("a", class_="productBtn")
            href = link_tag.get("href") if link_tag is not None else None
            if not isinstance(href, str) or not href:
                continue

            image_url: str | None = None
            image_wrapper = product_box.find("div", class_="productImg")
            if image_wrapper is not None:
                img_tag = image_wrapper.find("img")
                if img_tag is not None:
                    src = img_tag.get("src")
                    if isinstance(src, str) and src and not src.startswith("data:"):
                        image_url = src

            yield DiscountedProduct(
                uuid_=uuid.uuid7(),
                name=self.clean_discounted_product_name(text=name),
                real_price=real_price,
                discounted_price=discounted_price,
                url=href,
                image_url=image_url,
                created_at=start_date_of_collecting,
                updated_at=start_date_of_collecting,
                retailer_uuid=self._retailer.get_uuid(),
                category_uuid=None,
            )
            await asyncio.sleep(0.0)
