import asyncio
import datetime as dt
import logging
import re
import uuid
from collections.abc import AsyncIterator
from decimal import Decimal
from typing import ClassVar, override
from urllib.parse import urljoin

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


class RougeAmCollectorService(DiscountedProductCollectorService, DiscountedProductFieldsCleanerMixin):
    """Scrapes rouge.am's server-rendered ``/en/sale`` listing (a Next.js beauty/fragrance shop).

    The page is server-paginated with ``?page=N`` (~20 cards/page, ~400 items total), so we walk pages
    until one comes back with no product cards (bounded by ``MAX_PAGES`` as a safety net). Each card
    carries a brand line and a product-name line (joined into the display name), an original price, a
    discounted price, a product link and an image.

    Two site-specific quirks are handled here:
      * Prices group thousands with a dot ("205.000 ֏" = 205000 AMD, whole dram) — the shared price
        cleaner treats a dot as a decimal separator, so we collapse grouping to bare digits first.
      * Images are served through the Next.js image optimizer (``/_next/image?url=...``) on the standard
        host/port; it returns a PNG to a generic ``Accept`` header (only webp when the client advertises
        it), so the proxy URL is Telegram-safe and used as-is.

    The English listing is scraped because the Armenian ``/hy/sale`` page renders no cards server-side;
    the product names are latin brand/fragrance names regardless of locale.

    Category is not set here — rouge.am's whole catalog is beauty/fragrance, so it is configured with a
    fixed ``default_category`` on the retailer, which the collection use case stamps onto every product.
    """

    main_page_url: ClassVar[str] = "https://www.rouge.am"
    sale_page_url: ClassVar[str] = "https://www.rouge.am/en/sale"
    MAX_PAGES: ClassVar[int] = 40

    def __init__(
        self,
        retailer: Retailer,
    ) -> None:
        super().__init__(retailer=retailer)

    @override
    async def collect(self, start_date_of_collecting: dt.datetime) -> AsyncIterator[DiscountedProduct]:
        # rouge.am's page windows overlap at the boundaries (a product can appear on two consecutive
        # pages), so we track yielded product URLs and skip repeats to avoid duplicate rows.
        seen_urls: set[str] = set()
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0), follow_redirects=True) as client:
            for page in range(1, self.MAX_PAGES + 1):
                url_ = f"{self.sale_page_url}?page={page}"
                try:
                    response = await client.get(
                        url=url_,
                        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
                    )
                    response.raise_for_status()
                except httpx.InvalidURL as err:
                    logger.error(err)
                    raise InvalidUrlForScrappingError(invalid_url=url_) from err
                except Exception:
                    logger.exception("Request to rouge.am failed | page=%d", page)
                    break

                soup = BeautifulSoup(response.text, "lxml")
                product_cards = soup.find_all("div", class_="styles_product__9vFo0")
                # An empty page means we've walked past the last one — stop paginating.
                if not product_cards:
                    break

                for card in product_cards:
                    product = self.__parse_card(card, start_date_of_collecting)
                    if product is None:
                        continue
                    if product.get_url() in seen_urls:
                        continue
                    seen_urls.add(product.get_url())
                    yield product
                    await asyncio.sleep(0.0)

    def __parse_card(
        self, card: object, start_date_of_collecting: dt.datetime
    ) -> DiscountedProduct | None:
        brand_tag = card.find("p", class_="styles_brand_name__eOYXt")  # type: ignore[attr-defined]
        desc_tag = card.find("p", class_="styles_desc__5vujP")  # type: ignore[attr-defined]
        name = " ".join(
            tag.get_text(strip=True) for tag in (brand_tag, desc_tag) if tag is not None
        ).strip()
        if not name:
            return None

        old_price_tag = card.find("p", class_="styles_old_price__qBPfX")  # type: ignore[attr-defined]
        new_price_tag = card.find("p", class_="styles_discounted_price__fPfFL")  # type: ignore[attr-defined]
        # Both prices must be present for a card to count as a real discount.
        if old_price_tag is None or new_price_tag is None:
            return None
        real_price = self.__parse_amd_price(old_price_tag.get_text())
        discounted_price = self.__parse_amd_price(new_price_tag.get_text())
        if discounted_price <= 0 or real_price <= 0 or discounted_price >= real_price:
            return None

        link_tag = card.find("a", href=re.compile(r"/catalog/"))  # type: ignore[attr-defined]
        href = link_tag.get("href") if link_tag is not None else None
        if not isinstance(href, str) or not href:
            return None
        product_url = urljoin(self.main_page_url, href)

        image_url: str | None = None
        img_tag = card.find("img")  # type: ignore[attr-defined]
        if img_tag is not None:
            src = img_tag.get("src")
            if isinstance(src, str) and src and not src.startswith("data:"):
                image_url = urljoin(self.main_page_url, src)

        return DiscountedProduct(
            uuid_=uuid.uuid7(),
            name=self.clean_discounted_product_name(text=name),
            real_price=real_price,
            discounted_price=discounted_price,
            url=product_url,
            image_url=image_url,
            created_at=start_date_of_collecting,
            updated_at=start_date_of_collecting,
            retailer_uuid=self._retailer.get_uuid(),
            category_uuid=None,
        )

    def __parse_amd_price(self, text: str) -> Decimal:
        """Parse a rouge.am price string to a whole-dram ``Decimal``.

        Thousands are grouped with a dot ("205.000 ֏" = 205000), which the shared cleaner would read as
        a decimal point, so we collapse the string to bare digits before handing it over.

        Returns:
            The price in whole dram, or ``Decimal(0)`` if the string carried no digits.
        """
        digits = re.sub(r"[^\d]", "", text)
        return Decimal(self.clean_discounted_product_price(digits))
