"""Re-apply the category classifier to products already in the database.

Crawls classify products as they are collected; run this after editing category keywords/examples in
the Django admin (or changing ``CATEGORY_MATCH_*``) to apply the change to today's products without
waiting for the next crawl. Retailers with a fixed default category are left untouched.

``--dry-run`` classifies everything and prints what would change, without writing — use it to check a
keyword or threshold change against real data before applying it.

Usage (dev):
    ENV=dev python scripts/reclassify_categories.py --dry-run
    ENV=dev python scripts/reclassify_categories.py
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from metax.core.domain.entities.discounted_product.aggregate_root_entity import DiscountedProduct
from metax_bootstrap import METAX_LIFESPAN_MANAGER

logger = logging.getLogger("reclassify_categories")

_BATCH_SIZE = 500
_SAMPLES_PER_CATEGORY = 8


def _category_of(product: DiscountedProduct) -> UUID | None:
    return product.get_category_uuid() if product.has_category() else None


async def _reclassify(*, dry_run: bool) -> None:
    container = METAX_LIFESPAN_MANAGER.get_metax_container()
    classifier = container.get_category_classifier()
    uow = await container.get_unit_of_work_provider().provide()
    async with uow:
        categories = await uow.category_repo.all()
        retailers_with_fixed_category = {
            retailer.get_uuid()
            async for retailer in uow.retailer_repo.all()
            if retailer.get_default_category_uuid()
        }
        products = [
            product
            async for product in uow.discounted_product_repo.all()
            if product.get_retailer_uuid() not in retailers_with_fixed_category
        ]
    category_names: dict[UUID | None, str] = {category.get_uuid(): category.get_name() for category in categories}
    category_names[None] = "(uncategorised)"

    transitions: Counter[tuple[UUID | None, UUID | None]] = Counter()
    changed_by_new_category: dict[UUID | None, list[str]] = defaultdict(list)
    for start in range(0, len(products), _BATCH_SIZE):
        batch = products[start : start + _BATCH_SIZE]
        previous = [_category_of(product) for product in batch]
        for product in batch:
            product.clear_category()
        await classifier.classify_products(batch, categories)
        for product, before in zip(batch, previous, strict=True):
            after = _category_of(product)
            transitions[before, after] += 1
            if before != after:
                changed_by_new_category[after].append(f"{product.get_name()}  [was {category_names[before]}]")
        if not dry_run:
            uow = await container.get_unit_of_work_provider().provide()
            async with uow:
                await uow.discounted_product_repo.update_category_assignments(batch)
                await uow.commit()

    _print_report(transitions, changed_by_new_category, category_names, total=len(products), dry_run=dry_run)


def _print_report(
    transitions: Counter[tuple[UUID | None, UUID | None]],
    changed_by_new_category: dict[UUID | None, list[str]],
    category_names: dict[UUID | None, str],
    *,
    total: int,
    dry_run: bool,
) -> None:
    after_counts: Counter[UUID | None] = Counter()
    for (_before, after), count in transitions.items():
        after_counts[after] += count
    unchanged = sum(count for (before, after), count in transitions.items() if before == after)

    mode = "DRY RUN — nothing written" if dry_run else "Applied"
    lines = [
        f"\n{mode}: {total} products (excl. fixed-category retailers)",
        f"unchanged: {unchanged} | changed: {total - unchanged}\n",
        "Products per category after reclassification:",
    ]
    lines += [f"  {category_names[uuid_]:<28} {count:>6}" for uuid_, count in after_counts.most_common()]
    rng = random.Random(0)  # noqa: S311  # deterministic sampling for a readable report, not security
    for category_uuid, names in sorted(changed_by_new_category.items(), key=lambda item: -len(item[1])):
        lines.append(f"\n→ {category_names[category_uuid]}: {len(names)} changed, e.g.")
        lines += [f"    {name}" for name in rng.sample(names, min(_SAMPLES_PER_CATEGORY, len(names)))]
    sys.stdout.write("\n".join(lines) + "\n")


async def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="report what would change without writing")
    args = parser.parse_args()

    METAX_LIFESPAN_MANAGER.configure_django_app()
    METAX_LIFESPAN_MANAGER.configure_logger()
    await METAX_LIFESPAN_MANAGER.init_metax_container_resources()
    try:
        await _reclassify(dry_run=args.dry_run)
    finally:
        await METAX_LIFESPAN_MANAGER.shutdown_metax_container_resources()


if __name__ == "__main__":
    asyncio.run(_main())
