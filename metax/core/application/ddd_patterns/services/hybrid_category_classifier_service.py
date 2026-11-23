"""Product category classifier: exact keywords first, a strict embedding fallback second.

Precision beats coverage here — a product in the wrong category is worse than one with no category
(it still shows up in search; it just isn't listed when browsing a category). So classification runs
in tiers, strictest first, and a product nothing is sure about stays uncategorised:

1. **Keywords** (``CategoryKeywordMatcher``): a curated keyword in the product's noun phrase assigns
   that category outright, with distance ``0.0`` (full confidence). This is where most products are
   decided, and every decision is explainable by the keyword that matched.
2. **Embedding similarity** (optional, off by default — see ``embedding_fallback``), for the rest. The
   product's noun phrase (the name before the «brand»; the
   brand and size words only add noise) is compared to each category's prototypes — its localized
   names and curated ``examples`` — with the same multilingual model used for search. A category is
   assigned only if its nearest prototype is within ``max_distance`` **and** it beats the runner-up
   category by at least ``min_margin``; a product that sits between two categories is left alone.

The fallback is off by default because, measured on the collected data, it was right only about half
the time at any distance threshold: once keywords have taken the clear cases, what remains is exactly
what the embedding cannot tell apart. Products are embedded as documents and prototypes as queries,
mirroring the search read model (where product names are the indexed passages) so the two paths stay
consistent.
"""

from __future__ import annotations

import logging
from typing import override

import numpy as np

from metax.core.application.ddd_patterns.services.category_keyword_matcher import (
    CategoryKeywordMatcher,
    product_noun_phrase,
)
from metax.core.application.ports.ddd_patterns.service.category_classifier_service import (
    CategoryClassifierService,
)
from metax.core.application.ports.ddd_patterns.service.embedding_service import EmbeddingService
from metax.core.domain.entities.category.aggregate_root_entity import Category
from metax.core.domain.entities.discounted_product.aggregate_root_entity import DiscountedProduct

logger = logging.getLogger(__name__)

# Distance recorded for a keyword assignment: certain, so it ranks first within its category.
_KEYWORD_MATCH_DISTANCE = 0.0


def _category_text(category: Category) -> str:
    """Build the text embedded for a category from its available localized names.

    Returns:
        The category's names (``name / name_hy / name_ru``) joined, skipping empty ones.
    """
    names = [category.get_name(), category.get_name_hy(), category.get_name_ru()]
    return " / ".join(name for name in names if name)


def _category_prototypes(category: Category) -> list[str]:
    """All embedding anchor texts for a category: its localized label plus each curated example.

    Returns:
        The non-empty prototype texts (label first, then example product names).
    """
    return [text for text in [_category_text(category), *category.get_examples()] if text]


class HybridCategoryClassifierService(CategoryClassifierService):
    def __init__(
        self,
        embedding_service: EmbeddingService,
        *,
        embedding_fallback: bool = False,
        max_distance: float = 0.33,
        min_margin: float = 0.03,
    ) -> None:
        self._embedding_service = embedding_service
        self._embedding_fallback = embedding_fallback
        self._max_distance = max_distance
        self._min_margin = min_margin
        # Rebuilt only when a category's keywords, label or examples change (keyed by their content),
        # so every batch of a crawl — and later crawls — reuse the same matcher and prototype vectors.
        self._cache_key: tuple[object, ...] | None = None
        self._keyword_matcher = CategoryKeywordMatcher([])
        self._prototype_matrix = np.empty((0, 0), dtype=np.float32)
        # Maps each prototype row back to its category's index in the input list.
        self._prototype_category_indices = np.empty((0,), dtype=np.intp)

    @override
    async def classify_products(
        self,
        products: list[DiscountedProduct],
        categories: list[Category],
    ) -> None:
        if not categories or not products:
            return
        await self._prepare(categories)

        undecided: list[DiscountedProduct] = []
        for product in products:
            match = self._keyword_matcher.match(product.get_name())
            if match is None:
                undecided.append(product)
            else:
                product.set_category_uuid(match.category_uuid, distance=_KEYWORD_MATCH_DISTANCE)
        by_keyword = len(products) - len(undecided)

        by_embedding = await self._classify_by_embedding(undecided, categories)
        logger.info(
            "Category classifier: %d/%d by keyword, %d by embedding, %d left uncategorised",
            by_keyword,
            len(products),
            by_embedding,
            len(undecided) - by_embedding,
        )

    async def _classify_by_embedding(self, products: list[DiscountedProduct], categories: list[Category]) -> int:
        """Assign the products whose nearest category is both close enough and clearly ahead.

        Returns:
            How many products were assigned a category.
        """
        if not self._embedding_fallback or not products or self._prototype_matrix.shape[0] == 0:
            return 0
        vectors = await self._embedding_service.embed_documents([
            product_noun_phrase(p.get_name()) for p in products
        ])
        product_matrix = _l2_normalize(np.asarray(vectors, dtype=np.float32))

        # Cosine distance (1 - similarity) to every prototype in one matmul: (P, dim) @ (dim, N) -> (P, N),
        # then reduced to each product's distance to each *category* (its nearest prototype): (P, C).
        prototype_distances = 1.0 - product_matrix @ self._prototype_matrix.T
        category_distances = np.full((len(products), len(categories)), np.inf, dtype=np.float32)
        for category_index in range(len(categories)):
            columns = self._prototype_category_indices == category_index
            if columns.any():
                category_distances[:, category_index] = prototype_distances[:, columns].min(axis=1)

        assigned = 0
        for product, distances in zip(products, category_distances, strict=True):
            ranked = np.argsort(distances)
            best = int(ranked[0])
            best_distance = float(distances[best])
            runner_up_distance = float(distances[ranked[1]]) if len(ranked) > 1 else np.inf
            if best_distance > self._max_distance or runner_up_distance - best_distance < self._min_margin:
                continue
            product.set_category_uuid(categories[best].get_uuid(), distance=best_distance)
            assigned += 1
            logger.debug(
                "Classified %r → %r by embedding (distance %.3f, margin %.3f)",
                product.get_name(),
                categories[best].get_name(),
                best_distance,
                runner_up_distance - best_distance,
            )
        return assigned

    async def _prepare(self, categories: list[Category]) -> None:
        """Build the keyword matcher and embed the prototypes, reusing them while categories are unchanged."""
        prototype_texts: list[str] = []
        prototype_category_indices: list[int] = []
        for category_index, category in enumerate(categories):
            for text in _category_prototypes(category):
                prototype_texts.append(text)
                prototype_category_indices.append(category_index)

        cache_key = (
            tuple(prototype_texts),
            tuple(prototype_category_indices),
            tuple((category.get_uuid(), tuple(category.get_keywords())) for category in categories),
        )
        if cache_key == self._cache_key:
            return

        self._keyword_matcher = CategoryKeywordMatcher(categories)
        if prototype_texts and self._embedding_fallback:
            vectors = await self._embedding_service.embed_queries(prototype_texts)
            self._prototype_matrix = _l2_normalize(np.asarray(vectors, dtype=np.float32))
        else:
            self._prototype_matrix = np.empty((0, 0), dtype=np.float32)
        self._prototype_category_indices = np.asarray(prototype_category_indices, dtype=np.intp)
        self._cache_key = cache_key
        logger.info(
            "Category classifier: prepared %d keyword categories and %d embedding prototypes (cached)",
            sum(1 for category in categories if category.get_keywords()),
            len(prototype_texts),
        )


def _l2_normalize(matrix: np.ndarray) -> np.ndarray:
    """L2-normalize each row so a dot product equals cosine similarity.

    Returns:
        The row-normalized matrix; zero rows are left as zeros (they match nothing within the gate).
    """
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.where(norms == 0, 1.0, norms)
