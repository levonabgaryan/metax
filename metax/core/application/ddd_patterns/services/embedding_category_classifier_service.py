"""Embedding-based product category classifier.

Replaces the old generative (Ollama LLM) classifier. Instead of asking a language model to
pick a category number, it embeds each product name and each category label with the same
multilingual model used for vector search, then assigns every product to its nearest category
by cosine distance — provided that distance is within ``max_distance``. Products with no
sufficiently close category are left uncategorised.

Trade-off vs. the old LLM: an LLM *reasons* about a product ("Вино Արարատ" → Alcohol), whereas
this measures pure semantic similarity. To give the comparison the best chance, each category is
represented by several *prototypes* — its three localized names (``name / name_hy / name_ru``)
**and** any curated example product names (``Category.examples``). A product is assigned to the
category owning its single nearest prototype, so adding an example like ``կարագ`` to a category
makes products named ``կարագ`` snap to it (distance ≈ 0). ``max_distance`` is the lever to tune
against real data: lower it for stricter (fewer, more confident) assignments, raise it for more
coverage.

Products are embedded as documents and prototypes as queries, mirroring the search read model
(where product names are the indexed passages) so the two paths stay consistent.
"""

from __future__ import annotations

import logging
from typing import override

import numpy as np

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


def _category_prototypes(category: Category) -> list[str]:
    """All match-anchor texts for a category: its localized label plus each curated example.

    Returns:
        The non-empty prototype texts (label first, then example product names).
    """
    return [text for text in [_category_text(category), *category.get_examples()] if text]


class EmbeddingCategoryClassifierService(CategoryClassifierService):
    def __init__(self, embedding_service: EmbeddingService, max_distance: float = 0.45) -> None:
        self._embedding_service = embedding_service
        self._max_distance = max_distance
        # Prototype embeddings are reused across every batch of a crawl (and across crawls until a
        # category's label/examples change). Keyed by the embedded texts so an edit invalidates it.
        self._prototype_cache_key: tuple[str, ...] | None = None
        self._prototype_matrix: np.ndarray | None = None
        # Maps each prototype row back to its category's index in the input list.
        self._prototype_category_indices: np.ndarray | None = None

    @override
    async def classify_products(
        self,
        products: list[DiscountedProduct],
        categories: list[Category],
    ) -> None:
        if not categories or not products:
            return

        prototype_matrix, prototype_category_indices = await self._prototypes_for(categories)
        if prototype_matrix.shape[0] == 0:
            return
        product_vectors = await self._embedding_service.embed_documents([p.get_name() for p in products])
        product_matrix = _l2_normalize(np.asarray(product_vectors, dtype=np.float32))

        # Cosine distance (1 - similarity) between every product and every prototype in one matmul:
        # (P, dim) @ (dim, N) -> (P, N). Each product takes the category of its nearest prototype.
        distances = 1.0 - product_matrix @ prototype_matrix.T
        best_prototype = distances.argmin(axis=1)
        best_distances = distances[np.arange(distances.shape[0]), best_prototype]

        assigned = 0
        for product, prototype_index, best_distance in zip(products, best_prototype, best_distances, strict=True):
            if best_distance <= self._max_distance:
                category = categories[int(prototype_category_indices[prototype_index])]
                product.set_category_uuid(category.get_uuid(), distance=float(best_distance))
                assigned += 1
                logger.debug(
                    "Classified %r → %r (distance %.3f)",
                    product.get_name(), category.get_name(), float(best_distance),
                )

        logger.info("Embedding classifier: %d/%d products assigned a category", assigned, len(products))

    async def _prototypes_for(self, categories: list[Category]) -> tuple[np.ndarray, np.ndarray]:
        """Return the L2-normalized prototype matrix and its prototype→category index map.

        Embeds the prototypes once and caches them, recomputing only when a label or example changes.

        Returns:
            A ``(num_prototypes, dim)`` float32 matrix and a ``(num_prototypes,)`` int array mapping
            each row to its category index in ``categories``.
        """
        prototype_texts: list[str] = []
        category_indices: list[int] = []
        for category_index, category in enumerate(categories):
            for text in _category_prototypes(category):
                prototype_texts.append(text)
                category_indices.append(category_index)

        cache_key = tuple(prototype_texts)
        if (
            cache_key != self._prototype_cache_key
            or self._prototype_matrix is None
            or self._prototype_category_indices is None
        ):
            if prototype_texts:
                vectors = await self._embedding_service.embed_queries(prototype_texts)
                self._prototype_matrix = _l2_normalize(np.asarray(vectors, dtype=np.float32))
            else:
                self._prototype_matrix = np.empty((0, 0), dtype=np.float32)
            self._prototype_category_indices = np.asarray(category_indices, dtype=np.intp)
            self._prototype_cache_key = cache_key
            logger.info(
                "Embedding classifier: embedded %d prototypes for %d categories (cached for reuse)",
                len(prototype_texts),
                len(categories),
            )
        return self._prototype_matrix, self._prototype_category_indices


def _l2_normalize(matrix: np.ndarray) -> np.ndarray:
    """L2-normalize each row so a dot product equals cosine similarity.

    Returns:
        The row-normalized matrix; zero rows are left as zeros (they match nothing within the gate).
    """
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.where(norms == 0, 1.0, norms)
