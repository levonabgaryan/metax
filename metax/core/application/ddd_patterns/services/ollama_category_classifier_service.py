"""Ollama-based product category classifier.

Sends each product name to a local Ollama model along with the current
category list from the database.  The model is asked to return only a
category number — not a name — which eliminates text-matching ambiguity.

Prompt structure (built dynamically from real DB categories):

    Categories:
    1. Alcohol
    2. Dairy
    3. Meat & Fish
    4. None of the above

    Product: "Вино Арарат красное сухое 0.75л"

    Reply with ONE digit only. When uncertain, reply 4.

The response "1" maps directly back to the first Category UUID.
"""

from __future__ import annotations

import asyncio
import logging
import re

import httpx

from metax.core.domain.entities.category.aggregate_root_entity import Category
from metax.core.domain.entities.discounted_product.aggregate_root_entity import DiscountedProduct

logger = logging.getLogger(__name__)

_NUMBER_RE = re.compile(r"\b(\d+)\b")

_NONE_LABEL = "None of the above"


def build_prompt(product_name: str, categories: list[Category]) -> str:
    lines = [
        f"{i + 1}. {cat.get_name()} / {cat.get_name_hy()} / {cat.get_name_ru()}"
        for i, cat in enumerate(categories)
    ]
    none_index = len(categories) + 1
    lines.append(f"{none_index}. {_NONE_LABEL}")
    numbered = "\n".join(lines)
    return (
        f"Classify the product into a category number.\n"
        f"Rules:\n"
        f"- Pick a food, beverage, or personal care category ONLY if the product clearly belongs.\n"
        f"- Toys, games, puzzles, electronics, stationery, clothing → always pick {none_index}.\n"
        f"- When uncertain → pick {none_index}.\n\n"
        f"Categories:\n{numbered}\n\n"
        f'Product: "{product_name}"\n\n'
        f"Reply with ONE digit only. When uncertain, reply {none_index}."
    )


class OllamaCategoryClassifierService:
    def __init__(
        self,
        host: str,
        model: str,
        concurrency: int = 6,
        timeout: float = 10.0,
        classify_timeout: float = 300.0,
    ) -> None:
        self._host = host.rstrip("/")
        self._model = model
        self._semaphore = asyncio.Semaphore(concurrency)
        self._timeout = timeout
        self._classify_timeout = classify_timeout

    async def classify_products(
        self,
        products: list[DiscountedProduct],
        categories: list[Category],
    ) -> None:
        """Mutate ``products`` in-place, setting ``category_uuid`` where the model matches."""
        if not categories or not products:
            return

        results: list = []
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                async with asyncio.timeout(self._classify_timeout):
                    results = await asyncio.gather(
                        *[self._classify_one(client, p, categories) for p in products],
                        return_exceptions=True,
                    )
            except TimeoutError:
                logger.warning(
                    "Ollama: classification timed out after %.0fs — batch may be partially unclassified",
                    self._classify_timeout,
                )
                return

        failed = sum(1 for r in results if isinstance(r, Exception))
        assigned = sum(1 for p in products if p.has_category())
        logger.info(
            "Ollama: %d/%d assigned, %d failed",
            assigned, len(products), failed,
        )

    async def _classify_one(
        self,
        client: httpx.AsyncClient,
        product: DiscountedProduct,
        categories: list[Category],
    ) -> None:
        async with self._semaphore:
            prompt = build_prompt(product.get_name(), categories)
            raw = await self._call_ollama(client, prompt)
            category = _parse_response(raw, categories)
            if category is not None:
                product.set_category_uuid(category.get_uuid())
                logger.debug(
                    "Classified %r → %r",
                    product.get_name(), category.get_name(),
                )

    async def _call_ollama(self, client: httpx.AsyncClient, prompt: str) -> str:
        response = await client.post(
            f"{self._host}/api/generate",
            json={
                "model": self._model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0, "num_predict": 5},
            },
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()


def _parse_response(response: str, categories: list[Category]) -> Category | None:
    match = _NUMBER_RE.search(response)
    if not match:
        return None
    index = int(match.group(1))
    # 0 or the "None of the above" slot → no category
    if index == 0 or index > len(categories):
        return None
    return categories[index - 1]
