"""Telegram message formatters — HTML parse mode throughout."""

from __future__ import annotations

import html

from metax.core.application.read_models.discounted_product import DiscountedProductReadModel
from metax.frameworks_and_drivers.telegram_bot.localization import (
    DEFAULT_LANGUAGE,
    localized_category_name,
    retailer_display_name,
)

_MAX_NAME_LEN = 80


def get_first_image_url(products: list[DiscountedProductReadModel]) -> str | None:
    for p in products:
        url = p.get("image_url")
        if url:
            return url
    return None


def format_product(
    product: DiscountedProductReadModel, index: int, language_code: str = DEFAULT_LANGUAGE
) -> str:
    name = html.escape(product["name"][:_MAX_NAME_LEN])
    real_price = product["real_price"]
    discounted_price = product["discounted_price"]
    url = product["url"]
    retailer = html.escape(retailer_display_name(product["retailer"]["name"]))

    discount_pct = round((1 - discounted_price / real_price) * 100) if real_price > 0 else 0

    cat_line = ""
    if "category" in product:
        category = product["category"]
        category_name = localized_category_name(
            category["name"], category["name_hy"], category["name_ru"], language_code
        )
        cat_line = f"\n   🏷 {html.escape(category_name)}"

    return (
        f"<b>{index}. {name}</b>\n"
        f"   💸 <s>{real_price:,.0f}</s> → <b>{discounted_price:,.0f} ֏</b> <i>(-{discount_pct}%)</i>\n"
        f"   🏪 {retailer}{cat_line}\n"
        f'   <a href="{html.escape(url)}">Открыть →</a>'
    )
