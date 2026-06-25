"""Embedding-based product category classifier.

Replaces the old generative (Ollama LLM) classifier. Instead of asking a language model to
pick a category number, it embeds each product name and each category label with the same
multilingual model used for vector search, then assigns every product to its nearest category
by cosine distance — provided that distance is within ``max_distance``. Products with no
sufficiently close category are left uncategorised.

Trade-off vs. the old LLM: an LLM *reasons* about a product ("Вино Արարատ" → Alcohol), whereas
this measures pure semantic similarity between the product name and the category label. To give
the comparison the best chance, each category is embedded from its three localized names
(``name / name_hy / name_ru``). ``max_distance`` is the lever to tune against real data: lower
it for stricter (fewer, more confident) assignments, raise it for more coverage.

Products are embedded as documents and categories as queries, mirroring the search read model
(where product names are the indexed passages) so the two paths stay consistent.
"""

from __future__ import annotations

import logging
import math
from typing import override

from metax.core.application.ports.ddd_patterns.service.category_classifier_service import (
    CategoryClassifierService,
)
from metax.core.application.ports.ddd_patterns.service.embedding_service import EmbeddingService
from metax.core.domain.entities.category.aggregate_root_entity import Category
from metax.core.domain.entities.discounted_product.aggregate_root_entity import DiscountedProduct

logger = logging.getLogger(__name__)


def _category_text(category: Category) -> str:
    """Build the text embedded for a category from its available localized names.

    Returns:
        The category's names (``name / name_hy / name_ru``) joined, skipping empty ones.
    """
    names = [category.get_name(), category.get_name_hy(), category.get_name_ru()]
    return " / ".join(name for name in names if name)


def _cosine_distance(a: list[float], b: list[float]) -> float:
    """Cosine distance between two vectors; matches pgvector's ``<=>`` metric.

    Returns:
        A value in ``[0, 2]`` (0 = identical direction, 2 = opposite); 2.0 if either is zero.
    """
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if not norm_a or not norm_b:
        return 2.0
    return 1.0 - dot / (norm_a * norm_b)


class EmbeddingCategoryClassifierService(CategoryClassifierService):
    def __init__(self, embedding_service: EmbeddingService, max_distance: float = 0.45) -> None:
        self._embedding_service = embedding_service
        self._max_distance = max_distance

    @override
    async def classify_products(
        self,
        products: list[DiscountedProduct],
        categories: list[Category],
    ) -> None:
        if not categories or not products:
            return

        category_vectors = [await self._embedding_service.embed_query(_category_text(c)) for c in categories]
        product_vectors = await self._embedding_service.embed_documents([p.get_name() for p in products])

        assigned = 0
        for product, product_vector in zip(products, product_vectors, strict=True):
            best_index: int | None = None
            best_distance = math.inf
            for index, category_vector in enumerate(category_vectors):
                distance = _cosine_distance(product_vector, category_vector)
                if distance < best_distance:
                    best_distance = distance
                    best_index = index
            if best_index is not None and best_distance <= self._max_distance:
                category = categories[best_index]
                product.set_category_uuid(category.get_uuid())
                assigned += 1
                logger.debug(
                    "Classified %r → %r (distance %.3f)",
                    product.get_name(), category.get_name(), best_distance,
                )

        logger.info("Embedding classifier: %d/%d products assigned a category", assigned, len(products))
