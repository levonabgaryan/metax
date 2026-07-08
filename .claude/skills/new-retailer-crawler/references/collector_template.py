"""Fill-in-the-blanks template for a server-rendered HTML retailer collector.

Copy into
metax/frameworks_and_drivers/ddd_patterns/services/discounted_product_collector_services/<slug>.py
and replace every FOO / <...> marker. For a JSON-API source, adapt yerevan_city.py instead — do not
force HTML parsing onto an API.

Delete this docstring in the real file. Keep the structure (error handling, uuid7, field cleaning,
asyncio.sleep) identical to the sibling collectors — reviewers expect the shared shape.
"""

import asyncio
import datetime as dt
import logging
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

# A browser UA — many sites 403 the default httpx agent.
_HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}


class FooAmCollectorService(DiscountedProductCollectorService, DiscountedProductFieldsCleanerMixin):
    """One-line description of the source page and any quirks (ordering, placeholders, pagination)."""

    main_page_url: ClassVar[str] = "https://www.foo.am"
    discounted_products_page_url: ClassVar[str] = "https://www.foo.am/<discount-path>"

    def __init__(self, retailer: Retailer) -> None:
        super().__init__(retailer=retailer)

    @override
    async def collect(self, start_date_of_collecting: dt.datetime) -> AsyncIterator[DiscountedProduct]:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0), follow_redirects=True) as client:
            # If the site paginates, loop over offsets/pages here (see sas_am.py). Otherwise one GET.
            try:
                response = await client.get(url=self.discounted_products_page_url, headers=_HEADERS)
                response.raise_for_status()
            except httpx.InvalidURL as err:
                logger.error(err)
                raise InvalidUrlForScrappingError(invalid_url=self.discounted_products_page_url) from err
            except Exception:
                logger.exception("Request to foo.am failed")
                return

        soup = BeautifulSoup(response.text, "lxml")

        # <-- Replace with the real card container selector, confirmed against the fetched HTML.
        product_cards = soup.find_all("div", class_="<product-card-class>")

        for card in product_cards:
            # Skip out-of-stock / unavailable cards — the user can't buy them.
            # if card.find("span", class_="<unavailable-class>") is not None:
            #     continue

            name_tag = card.find("<name-tag>", class_="<name-class>")
            if name_tag is None:
                continue
            name = name_tag.get_text(strip=True)
            if not name:
                continue

            # Prices. If the two price spans are NOT reliably ordered, use max/min (see tntesakan_am.py).
            old_tag = card.find("<tag>", class_="<old-price-class>")
            new_tag = card.find("<tag>", class_="<new-price-class>")
            if old_tag is None or new_tag is None:
                continue
            real_price = Decimal(self.clean_discounted_product_price(old_tag.get_text(strip=True)))
            discounted_price = Decimal(self.clean_discounted_product_price(new_tag.get_text(strip=True)))
            if discounted_price <= 0 or real_price <= 0:
                continue

            link_tag = card.find("a", class_="<link-class>")
            href = link_tag.get("href") if link_tag is not None else None
            if not isinstance(href, str) or not href:
                continue
            product_url = urljoin(self.main_page_url, href)

            image_url = self._extract_image_url(card)

            yield DiscountedProduct(
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
            await asyncio.sleep(0.0)

    def _extract_image_url(self, card: BeautifulSoup) -> str | None:
        """Return an absolute, Telegram-safe image URL, or None. Handle lazy-load + placeholders.

        See SKILL.md Step 3. Prefer data-src over src; reject data: URIs; resolve relatives; if the
        site uses <picture>/framework tags with a JSON sources payload, parse that first.
        """
        img_tag = card.find("img")
        if img_tag is None:
            return None
        # Lazy-loaded pages put the real URL in data-src; src is often a placeholder.
        src = img_tag.get("data-src") or img_tag.get("src")
        if not isinstance(src, str) or not src or src.startswith("data:"):
            return None
        return urljoin(self.main_page_url, src)
