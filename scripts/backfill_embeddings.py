"""One-off backfill: embed all discounted products whose ``name_embedding`` is NULL.

Use when a collection run saved products but the embedding step failed (e.g. a
``ReadTimeout`` on a cold model load), leaving rows pending. Idempotent:
``embed_pending`` only fetches rows still missing a vector, so re-running is safe.

Usage (dev):
    ENV=dev python scripts/backfill_embeddings.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from metax_bootstrap import METAX_LIFESPAN_MANAGER

logger = logging.getLogger("backfill_embeddings")


async def _main() -> None:
    METAX_LIFESPAN_MANAGER.configure_django_app()
    METAX_LIFESPAN_MANAGER.configure_logger()
    await METAX_LIFESPAN_MANAGER.init_metax_container_resources()
    container = METAX_LIFESPAN_MANAGER.get_metax_container()
    repo = await container.get_discounted_product_read_model_repository()

    logger.info("Backfill started — embedding pending products…")
    embedded = await repo.embed_pending()
    logger.info("Backfill done — embedded %s product(s).", embedded)

    await METAX_LIFESPAN_MANAGER.shutdown_metax_container_resources()


if __name__ == "__main__":
    asyncio.run(_main())
