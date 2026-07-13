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


class VlvAmCollectorService(DiscountedProductCollectorService, DiscountedProductFieldsCleanerMixin):
    """Collects vlv.am discounts from the JSON API backing its React storefront.

    vlv.am renders client-side, so there is no HTML to scrape: the ``/sales/discount`` page POSTs to
    ``v1.vlv.am/api/category/discounted-products`` with ``d=1&discountSales=1`` and pages through the
    result 20 products at a time. The page size is fixed server-side (``paginate`` is ignored), so the
    full catalogue takes ~64 requests. Those must be issued **sequentially** — the API answers 429 to
    concurrent bursts.

    Product names are assembled the way the storefront's cards display them: Armenian category name,
    brand, then model, e.g. ``Թերմոսներ LARA LR04-33``. A product's public page is keyed by
    ``seller_id``, not by ``id`` or ``slug``.

    Images are webp on an origin Telegram cannot reliably fetch, so ``vlv.am`` is registered in the
    bot's ``_TELEGRAM_UNFETCHABLE_IMAGE_HOSTS`` and mirrored through the weserv CDN as JPEG.
    """

    discounted_products_api_url: ClassVar[str] = "https://v1.vlv.am/api/category/discounted-products"
    product_page_base_url: ClassVar[str] = "https://vlv.am/Product"
    image_base_url: ClassVar[str] = "https://vlv.am/public/"

    # The API rejects bursts with 429; pace sequential page requests instead.
    DELAY_BETWEEN_PAGES_SECONDS: ClassVar[float] = 0.3
    # Guard against a malformed ``lastPage`` sending us into an unbounded paging loop.
    MAX_PAGES: ClassVar[int] = 200

    def __init__(
        self,
        retailer: Retailer,
    ) -> None:
        super().__init__(retailer=retailer)

    @override
    async def collect(self, start_date_of_collecting: dt.datetime) -> AsyncIterator[DiscountedProduct]:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
        ) as client:
            page = 1
            last_page = 1

            while page <= min(last_page, self.MAX_PAGES):
                try:
                    response = await client.post(
                        url=self.discounted_products_api_url,
                        files={
                            "d": (None, "1"),
                            "discountSales": (None, "1"),
                            "page": (None, str(page)),
                        },
                    )
                    response.raise_for_status()
                    payload = response.json()
                except httpx.InvalidURL as err:
                    logger.error(err)
                    raise InvalidUrlForScrappingError(invalid_url=self.discounted_products_api_url) from err
                except Exception:
                    logger.exception("Request to vlv.am failed | page=%d", page)
                    return

                last_page = payload.get("lastPage") or last_page

                for raw_product in payload.get("products", []):
                    product = self.__build_discounted_product(
                        raw_product=raw_product,
                        start_date_of_collecting=start_date_of_collecting,
                    )
                    if product is None:
                        continue
                    yield product
                    await asyncio.sleep(0.0)

                page += 1
                await asyncio.sleep(self.DELAY_BETWEEN_PAGES_SECONDS)

    def __build_discounted_product(
        self,
        raw_product: dict[str, Any],
        start_date_of_collecting: dt.datetime,
    ) -> DiscountedProduct | None:
        pricing = raw_product.get("pricing") or {}
        selling_price = pricing.get("selling_price")
        promo_price = pricing.get("promo_price")
        seller_id = raw_product.get("seller_id")
        if not selling_price or not promo_price or not seller_id:
            return None

        real_price = Decimal(self.clean_discounted_product_price(selling_price))
        discounted_price = Decimal(self.clean_discounted_product_price(promo_price))
        if discounted_price <= 0 or discounted_price >= real_price:
            return None

        name = self.__build_name(raw_product=raw_product)
        if not name:
            return None

        return DiscountedProduct(
            uuid_=uuid.uuid7(),
            name=self.clean_discounted_product_name(text=name),
            real_price=real_price,
            discounted_price=discounted_price,
            url=f"{self.product_page_base_url}/{seller_id}",
            image_url=self.__build_image_url(raw_product=raw_product),
            created_at=start_date_of_collecting,
            updated_at=start_date_of_collecting,
            retailer_uuid=self._retailer.get_uuid(),
            category_uuid=None,
        )

    @staticmethod
    def __build_name(raw_product: dict[str, Any]) -> str:
        """Compose the name the storefront's product card shows: category, brand, then model.

        Returns:
            The space-joined name, omitting any part the API left empty.
        """
        category_name = (raw_product.get("category") or {}).get("name_hy") or ""
        brand_name = (raw_product.get("brand") or {}).get("name") or ""
        model_name = raw_product.get("product_name") or ""
        return " ".join(part for part in (category_name, brand_name, model_name) if part)

    @classmethod
    def __build_image_url(cls, raw_product: dict[str, Any]) -> str | None:
        """Resolve the card thumbnail, falling back to the first gallery image when it is absent.

        Returns:
            The absolute image URL, or ``None`` when the product carries no usable image.
        """
        source = raw_product.get("thumbnail_image_source")
        if not source:
            media = raw_product.get("media") or []
            source = media[0].get("images_source") if media else None
        if not isinstance(source, str) or not source or source.startswith("data:"):
            return None
        return f"{cls.image_base_url}{source.lstrip('/')}"
