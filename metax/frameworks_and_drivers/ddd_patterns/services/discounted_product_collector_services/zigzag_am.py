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
from bs4 import BeautifulSoup, Tag

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

# A browser UA — the default httpx agent is a candidate for a 403.
_HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}


class ZigzagAmCollectorService(DiscountedProductCollectorService, DiscountedProductFieldsCleanerMixin):
    """Collects zigzag.am discounts from its current promo-campaign pages (Magento storefront).

    zigzag.am has no single "all discounts" listing — the full catalogue is ~15k products across
    deeply paginated categories, and its ``outlet`` category is demo-unit clearance without crossed-out
    prices. What it *does* expose is a promo hub at ``/am/promo.html`` linking every currently-running
    campaign (slugs live under ``/am/promo/current…/``), and each campaign page is a normal product
    grid. So we crawl those campaign pages and keep only the cards that render a live discount.

    A card is "discounted" when Magento renders both an ``oldPrice`` span (the crossed-out original)
    and a ``finalPrice`` span (the special price). Magento only renders ``oldPrice`` while the special
    price is inside its ``special_from_date``/``special_to_date`` window, so filtering on its presence
    means an expired campaign that still has a live page contributes nothing — the daily crawl
    self-expires stale deals without us tracking any dates. The clean numeric value lives in each
    span's ``data-price-amount`` attribute (the visible text carries thousands separators and the ``֏``
    sign). Products recur across overlapping campaigns, so we dedupe by Magento product id.

    Category is not set here — categorization happens downstream (see CollectDiscountedProducts).
    """

    main_page_url: ClassVar[str] = "https://www.zigzag.am"
    promo_index_url: ClassVar[str] = "https://www.zigzag.am/am/promo.html"

    # Only campaigns linked from the promo hub, and only the localized product-grid ones.
    _CAMPAIGN_URL_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"https://www\.zigzag\.am/am/promo/current[^\"']+\.html"
    )
    # Magento's page-size options; 36 is the largest allowed, so it minimises requests per campaign.
    _PRODUCT_LIST_LIMIT: ClassVar[int] = 36
    # Guard against a pager that keeps advancing (Magento clamps ``p`` past the last page rather than
    # dropping the "Next" link), on top of the visited-URL loop check.
    _MAX_PAGES_PER_CAMPAIGN: ClassVar[int] = 100

    def __init__(
        self,
        retailer: Retailer,
    ) -> None:
        super().__init__(retailer=retailer)

    @override
    async def collect(self, start_date_of_collecting: dt.datetime) -> AsyncIterator[DiscountedProduct]:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(60.0), follow_redirects=True, headers=_HEADERS
        ) as client:
            try:
                index_response = await client.get(url=self.promo_index_url)
                index_response.raise_for_status()
            except httpx.InvalidURL as err:
                logger.error(err)
                raise InvalidUrlForScrappingError(invalid_url=self.promo_index_url) from err
            except Exception:
                logger.exception("Request to zigzag.am promo index failed")
                return

            campaign_urls = sorted(set(self._CAMPAIGN_URL_RE.findall(index_response.text)))

            seen_product_ids: set[str] = set()
            for campaign_url in campaign_urls:
                async for product in self.__collect_campaign(
                    client=client,
                    campaign_url=campaign_url,
                    seen_product_ids=seen_product_ids,
                    start_date_of_collecting=start_date_of_collecting,
                ):
                    yield product
                    await asyncio.sleep(0.0)

    async def __collect_campaign(
        self,
        client: httpx.AsyncClient,
        campaign_url: str,
        seen_product_ids: set[str],
        start_date_of_collecting: dt.datetime,
    ) -> AsyncIterator[DiscountedProduct]:
        """Yield the discounted, not-yet-seen products from one campaign, following its pagination.

        A failed page request is logged and ends this campaign (``return``) rather than crashing the
        whole run — the remaining campaigns still get crawled.
        """
        url: str | None = f"{campaign_url}?product_list_limit={self._PRODUCT_LIST_LIMIT}"
        visited: set[str] = set()

        while url is not None and url not in visited and len(visited) < self._MAX_PAGES_PER_CAMPAIGN:
            visited.add(url)
            try:
                response = await client.get(url=url)
                response.raise_for_status()
            except Exception:
                logger.exception("Request to zigzag.am campaign page failed | url=%s", url)
                return

            soup = BeautifulSoup(response.text, "lxml")
            for card in soup.find_all("div", class_="product_block"):
                product = self.__build_discounted_product(
                    card=card,
                    seen_product_ids=seen_product_ids,
                    start_date_of_collecting=start_date_of_collecting,
                )
                if product is not None:
                    yield product

            url = self.__find_next_page_url(response.text)

    def __build_discounted_product(
        self,
        card: Tag,
        seen_product_ids: set[str],
        start_date_of_collecting: dt.datetime,
    ) -> DiscountedProduct | None:
        """Turn one product card into a ``DiscountedProduct``, or ``None`` if it is not a live deal.

        Returns:
            The built ``DiscountedProduct``, or ``None`` for cards without a crossed-out ``oldPrice``
            (not currently discounted), with an unparseable price, or whose product id was already
            yielded by an earlier campaign.
        """
        old_price_span = card.find("span", attrs={"data-price-type": "oldPrice"})
        final_price_span = card.find("span", attrs={"data-price-type": "finalPrice"})
        if not isinstance(old_price_span, Tag) or not isinstance(final_price_span, Tag):
            return None

        real_price = self.__price_from_span(old_price_span)
        discounted_price = self.__price_from_span(final_price_span)
        if real_price <= 0 or discounted_price <= 0 or discounted_price >= real_price:
            return None

        product_id = str(card.get("id") or "").rsplit("_", 1)[-1]
        if not product_id or product_id in seen_product_ids:
            return None

        link = card.find("a", class_="product_name")
        if not isinstance(link, Tag):
            return None
        name = link.get_text(strip=True)
        href = link.get("href")
        if not name or not isinstance(href, str) or not href:
            return None

        seen_product_ids.add(product_id)
        return DiscountedProduct(
            uuid_=uuid.uuid7(),
            name=self.clean_discounted_product_name(text=name),
            real_price=real_price,
            discounted_price=discounted_price,
            url=urljoin(self.main_page_url, href),
            image_url=self.__extract_image_url(card),
            created_at=start_date_of_collecting,
            updated_at=start_date_of_collecting,
            retailer_uuid=self._retailer.get_uuid(),
            category_uuid=None,
        )

    def __price_from_span(self, price_span: Tag) -> Decimal:
        """Read a price from a Magento price span, preferring its clean ``data-price-amount`` attribute.

        Returns:
            The parsed price, or ``Decimal(0)`` when neither the attribute nor the text is usable.
        """
        amount = price_span.get("data-price-amount")
        raw = amount if isinstance(amount, str) and amount else price_span.get_text(strip=True)
        return Decimal(self.clean_discounted_product_price(raw))

    def __extract_image_url(self, card: Tag) -> str | None:
        """Return the product's image URL from the card's image block, or ``None``.

        The first ``img`` in a card is the promo/outlet sticker badge, so we scope to ``.image_block``.
        Its ``src`` already holds the real (non-placeholder) catalog URL; ``data-src`` is preferred in
        case a page lazy-loads.
        """
        image_block = card.find("div", class_="image_block")
        if not isinstance(image_block, Tag):
            return None
        img = image_block.find("img")
        if not isinstance(img, Tag):
            return None
        src = img.get("data-src") or img.get("src")
        if not isinstance(src, str) or not src or src.startswith("data:"):
            return None
        return urljoin(self.main_page_url, src)

    @staticmethod
    def __find_next_page_url(html: str) -> str | None:
        """Extract the pager's absolute "Next" URL, or ``None`` on the last page.

        Returns:
            The unescaped Next-page URL when present, else ``None``.
        """
        match = re.search(r'href="([^"]+)"[^>]*\btitle="Next"', html)
        if match is None:
            return None
        return match.group(1).replace("&amp;", "&")
