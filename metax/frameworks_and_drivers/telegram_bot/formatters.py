"""Telegram message formatters — HTML parse mode throughout."""

from __future__ import annotations

import html

from metax.core.application.read_models.discounted_product import DiscountedProductReadModel

_MAX_NAME_LEN = 80


def get_first_image_url(products: list[DiscountedProductReadModel]) -> str | None:
    for p in products:
        url = p.get("image_url")
        if url:
            return url
    return None


def format_product(product: DiscountedProductReadModel, index: int) -> str:
    name = html.escape(product["name"][:_MAX_NAME_LEN])
    real_price = product["real_price"]
    discounted_price = product["discounted_price"]
    url = product["url"]
    retailer = html.escape(product["retailer"]["name"])

    discount_pct = round((1 - discounted_price / real_price) * 100) if real_price > 0 else 0

    cat_line = ""
    if "category" in product:
        cat_line = f"\n   🏷 {html.escape(product['category']['name'])}"
        # When browsing a category, show how sure the classifier is this product belongs here.
        if "category_confidence" in product:
            cat_line += f" · 🎯 {round(product['category_confidence'] * 100)}%"

    # On a name/phonetic search, show how closely the product matched the query.
    match_line = ""
    if "match_confidence" in product:
        match_line = f"\n   🎯 {round(product['match_confidence'] * 100)}%"

    return (
        f"<b>{index}. {name}</b>\n"
        f"   💸 <s>{real_price:,.0f}</s> → <b>{discounted_price:,.0f} ֏</b> <i>(-{discount_pct}%)</i>\n"
        f"   🏪 {retailer}{cat_line}{match_line}\n"
        f'   <a href="{html.escape(url)}">Открыть →</a>'
    )
