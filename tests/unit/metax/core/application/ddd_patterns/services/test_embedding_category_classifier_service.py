"""Unit tests for the embedding-based category classifier (no real embeddings service).

A fake ``EmbeddingService`` returns fixed vectors so we can assert the nearest-category logic, the
``max_distance`` gate, and that category embeddings are computed once and reused across batches.
"""

from __future__ import annotations

import datetime as dt
from typing import override

import pytest

from metax.core.application.ddd_patterns.services.embedding_category_classifier_service import (
    EmbeddingCategoryClassifierService,
)
from metax.core.application.ports.ddd_patterns.service.embedding_service import EmbeddingService
from metax.core.domain.entities.discounted_product.aggregate_root_entity import DiscountedProduct
from tests.utils import make_category_entity, make_discounted_product_entity, make_retailer_entity


class _FakeEmbeddingService(EmbeddingService):
    """Maps known texts to fixed unit vectors; counts how often queries are embedded."""

    def __init__(self, vectors_by_text: dict[str, list[float]]) -> None:
        self._vectors = vectors_by_text
        self.embed_queries_calls = 0

    @property
    @override
    def dimensions(self) -> int:
        return 3

    @override
    async def embed_query(self, text: str) -> list[float]:
        return self._vectors[text]

    @override
    async def embed_queries(self, texts: list[str]) -> list[list[float]]:
        self.embed_queries_calls += 1
        return [self._vectors[text] for text in texts]

    @override
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vectors[text] for text in texts]


def _product(name: str) -> DiscountedProduct:
    retailer = make_retailer_entity()
    return make_discounted_product_entity(
        retailer_uuid=retailer.get_uuid(), created_at=dt.datetime.now(tz=dt.UTC), name=name
    )


async def test_assigns_nearest_category_and_gates_on_distance() -> None:
    # given: "milk" is identical to the dairy vector; "screwdriver" is orthogonal to every category
    dairy = make_category_entity(name="dairy")
    meat = make_category_entity(name="meat")
    fake = _FakeEmbeddingService(
        {
            "dairy": [1.0, 0.0, 0.0],
            "meat": [0.0, 1.0, 0.0],
            "milk": [1.0, 0.0, 0.0],
            "screwdriver": [0.0, 0.0, 1.0],
        }
    )
    classifier = EmbeddingCategoryClassifierService(embedding_service=fake, max_distance=0.45)
    milk = _product("milk")
    screwdriver = _product("screwdriver")

    # when
    await classifier.classify_products([milk, screwdriver], [dairy, meat])

    # then: the close product is categorised (with its match distance recorded ≈ 0), the far one
    # is left untouched (distance 1.0 > 0.45)
    assert milk.get_category_uuid() == dairy.get_uuid()
    assert milk.get_category_distance() == pytest.approx(0.0, abs=1e-6)
    assert not screwdriver.has_category()
    assert screwdriver.get_category_distance() is None


async def test_example_product_name_anchors_a_match_the_label_alone_would_miss() -> None:
    # given: "կարագ" is far from the "dairy" label vector (would be left uncategorised)...
    dairy = make_category_entity(name="dairy")
    fake = _FakeEmbeddingService(
        {
            "dairy": [1.0, 0.0, 0.0],
            "կարագ": [0.0, 1.0, 0.0],  # both the example prototype and the product embed to this
        }
    )
    classifier = EmbeddingCategoryClassifierService(embedding_service=fake, max_distance=0.45)
    butter = _product("կարագ")

    # without the example: the label is orthogonal to the product -> no category
    await classifier.classify_products([butter], [dairy])
    assert not butter.has_category()

    # ...but adding "կարագ" as an example of dairy makes the product snap to it (distance ≈ 0)
    dairy.set_examples(["կարագ"])
    butter_again = _product("կարագ")
    await classifier.classify_products([butter_again], [dairy])
    assert butter_again.get_category_uuid() == dairy.get_uuid()


async def test_category_embeddings_are_computed_once_across_batches() -> None:
    # given
    dairy = make_category_entity(name="dairy")
    fake = _FakeEmbeddingService({"dairy": [1.0, 0.0, 0.0], "milk": [1.0, 0.0, 0.0]})
    classifier = EmbeddingCategoryClassifierService(embedding_service=fake, max_distance=0.45)

    # when: two separate batches are classified against the same categories
    await classifier.classify_products([_product("milk")], [dairy])
    await classifier.classify_products([_product("milk")], [dairy])

    # then: categories were embedded only on the first batch (cached afterwards)
    assert fake.embed_queries_calls == 1
