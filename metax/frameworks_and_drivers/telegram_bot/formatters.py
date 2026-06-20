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

    return (
        f"<b>{index}. {name}</b>\n"
        f"   💸 <s>{real_price:,.0f}</s> → <b>{discounted_price:,.0f} ֏</b> <i>(-{discount_pct}%)</i>\n"
        f"   🏪 {retailer}{cat_line}\n"
        f'   <a href="{html.escape(url)}">Открыть →</a>'
    )


def format_search_results(
    products: list[DiscountedProductReadModel],
    query: str,
    total: int,
    offset: int,
    limit: int,
) -> str:
    header = f"🔍 <b>«{html.escape(query)}»</b> — найдено: {total}\n"
    if not products:
        return f"{header}\nПо этому запросу ничего не найдено."

    page = offset // limit + 1
    total_pages = max(1, (total + limit - 1) // limit)
    lines = [header]
    for i, p in enumerate(products, start=offset + 1):
        lines.append(format_product(p, i))
    lines.append(f"\nСтраница {page} / {total_pages}")
    return "\n\n".join(lines)


def format_category_results(
    products: list[DiscountedProductReadModel],
    category_name: str,
    total: int,
    offset: int,
    limit: int,
) -> str:
    header = f"🏷 <b>{html.escape(category_name)}</b> — товаров: {total}\n"
    if not products:
        return f"{header}\nВ этой категории пока нет товаров."

    page = offset // limit + 1
    total_pages = max(1, (total + limit - 1) // limit)
    lines = [header]
    for i, p in enumerate(products, start=offset + 1):
        lines.append(format_product(p, i))
    lines.append(f"\nСтраница {page} / {total_pages}")
    return "\n\n".join(lines)
