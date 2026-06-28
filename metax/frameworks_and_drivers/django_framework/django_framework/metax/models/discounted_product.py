from __future__ import annotations

from typing import override

from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django_stubs_ext.db.models import TypedModelMeta
from pgvector.django import HnswIndex, VectorField

from .base_model import BaseDbModel

# Embedding dimension for semantic search. Must match metax_configs EMBEDDING_DIM and the
# embedding model's output (armenian-text-embeddings-2-large -> 1024).
NAME_EMBEDDING_DIMENSIONS = 1024


class DiscountedProductModel(BaseDbModel):
    uuid = models.UUIDField(primary_key=True, editable=False)
    real_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    name = models.CharField(max_length=128, null=False)
    # Latin phonetic transliteration of ``name`` for cross-script search ("karag" matching "կարագ").
    # Filled at insert time; NULL only for rows that predate this column.
    name_translit = models.CharField(max_length=256, null=True, blank=True)  # noqa: DJ001
    url = models.URLField(max_length=2048)
    # image_url is genuinely optional; a nullable column matches the domain (None vs. empty string).
    image_url = models.URLField(max_length=2048, null=True, blank=True)  # noqa: DJ001

    # Semantic-search vector of ``name``; NULL until the embedding worker fills it after a crawl.
    name_embedding = VectorField(dimensions=NAME_EMBEDDING_DIMENSIONS, null=True, blank=True)

    category = models.ForeignKey(
        "CategoryModel",
        on_delete=models.SET_NULL,
        db_column="category_uuid",
        null=True,
        blank=True,
    )
    retailer = models.ForeignKey("RetailerModel", on_delete=models.CASCADE, db_column="retailer_uuid")

    class Meta(TypedModelMeta):
        db_table = "discounted_products"
        verbose_name = "discounted product"
        verbose_name_plural = "discounted products"
        indexes = [  # noqa: RUF012
            # Approximate-nearest-neighbour (cosine) index for semantic search.
            HnswIndex(
                name="dp_name_embedding_hnsw",
                fields=["name_embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
            # Trigram index backing the exact/substring (ILIKE) search boost.
            GinIndex(
                name="dp_name_trgm_gin",
                fields=["name"],
                opclasses=["gin_trgm_ops"],
            ),
            # Same trigram boost for the transliterated name (cross-script phonetic search).
            GinIndex(
                name="dp_name_translit_trgm_gin",
                fields=["name_translit"],
                opclasses=["gin_trgm_ops"],
            ),
        ]

    @override
    def __str__(self) -> str:
        return f"{self.name} ({self.uuid})"
