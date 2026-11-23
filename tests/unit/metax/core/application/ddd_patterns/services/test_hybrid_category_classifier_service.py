"""Unit tests for the keyword-first category classifier (no real embeddings service).

A fake ``EmbeddingService`` returns fixed vectors so we can assert the keyword tier, the optional
embedding fallback (nearest category, ``max_distance`` and ``min_margin`` gates), and that category
embeddings are computed once and reused across batches.
"""

from __future__ import annotations

import datetime as dt
from typing import override

import pytest

from metax.core.application.ddd_patterns.services.hybrid_category_classifier_service import (
    HybridCategoryClassifierService,
)
from metax.core.application.ports.ddd_patterns.service.embedding_service import EmbeddingService
from metax.core.domain.entities.discounted_product.aggregate_root_entity import DiscountedProduct
from tests.utils import make_category_entity, make_discounted_product_entity, make_retailer_entity


class _FakeEmbeddingService(EmbeddingService):
    """Maps known texts to fixed unit vectors; counts how often texts are embedded."""

    def __init__(self, vectors_by_text: dict[str, list[float]]) -> None:
        self._vectors = vectors_by_text
        self.embed_queries_calls = 0
        self.embed_documents_calls = 0

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
        self.embed_documents_calls += 1
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
    fake = _FakeEmbeddingService({
        "dairy": [1.0, 0.0, 0.0],
        "meat": [0.0, 1.0, 0.0],
        "milk": [1.0, 0.0, 0.0],
        "screwdriver": [0.0, 0.0, 1.0],
    })
    classifier = HybridCategoryClassifierService(
        embedding_service=fake, embedding_fallback=True, max_distance=0.45
    )
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
    fake = _FakeEmbeddingService({
        "dairy": [1.0, 0.0, 0.0],
        "կարագ": [0.0, 1.0, 0.0],  # both the example prototype and the product embed to this
    })
    classifier = HybridCategoryClassifierService(
        embedding_service=fake, embedding_fallback=True, max_distance=0.45
    )
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
    classifier = HybridCategoryClassifierService(
        embedding_service=fake, embedding_fallback=True, max_distance=0.45
    )

    # when: two separate batches are classified against the same categories
    await classifier.classify_products([_product("milk")], [dairy])
    await classifier.classify_products([_product("milk")], [dairy])

    # then: categories were embedded only on the first batch (cached afterwards)
    assert fake.embed_queries_calls == 1


async def test_keyword_decides_with_full_confidence_and_skips_embedding() -> None:
    # given: a keyword for dairy; the embedding fallback is off (the default)
    dairy = make_category_entity(name="dairy")
    dairy.set_keywords(["պանիր"])
    fake = _FakeEmbeddingService({})
    classifier = HybridCategoryClassifierService(embedding_service=fake)
    cheese = _product("Պանիր հալած «Հոխլանդ» 140գր")
    unknown = _product("Ծաղկեփունջ «Rose»")

    # when
    await classifier.classify_products([cheese, unknown], [dairy])

    # then: the keyword match is certain (distance 0), the rest stays uncategorised, nothing was embedded
    assert cheese.get_category_uuid() == dairy.get_uuid()
    assert cheese.get_category_distance() == pytest.approx(0.0)
    assert not unknown.has_category()
    assert fake.embed_documents_calls == 0
    assert fake.embed_queries_calls == 0


async def test_keyword_beats_a_closer_embedding_match() -> None:
    # given: the product's embedding is identical to "meat", but a keyword says dairy
    dairy = make_category_entity(name="dairy")
    meat = make_category_entity(name="meat")
    dairy.set_keywords(["կարագ"])
    fake = _FakeEmbeddingService({"dairy": [1.0, 0.0, 0.0], "meat": [0.0, 1.0, 0.0], "կարագ": [0.0, 1.0, 0.0]})
    classifier = HybridCategoryClassifierService(
        embedding_service=fake, embedding_fallback=True, max_distance=0.45
    )
    butter = _product("կարագ")

    # when
    await classifier.classify_products([butter], [dairy, meat])

    # then
    assert butter.get_category_uuid() == dairy.get_uuid()


async def test_embedding_fallback_leaves_a_product_between_two_categories_uncategorised() -> None:
    # given: the product is equally close to both categories (no margin between them)
    dairy = make_category_entity(name="dairy")
    meat = make_category_entity(name="meat")
    fake = _FakeEmbeddingService({
        "dairy": [1.0, 0.0, 0.0],
        "meat": [0.0, 1.0, 0.0],
        "ambiguous": [0.7071, 0.7071, 0.0],
    })
    classifier = HybridCategoryClassifierService(
        embedding_service=fake, embedding_fallback=True, max_distance=0.45, min_margin=0.03
    )
    product = _product("ambiguous")

    # when
    await classifier.classify_products([product], [dairy, meat])

    # then: close enough to both (distance ≈ 0.29), but neither is clearly ahead
    assert not product.has_category()


async def test_embedding_fallback_embeds_only_the_noun_phrase_not_the_brand() -> None:
    # given: only the noun phrase has a vector, so embedding the full name would raise KeyError
    dairy = make_category_entity(name="dairy")
    fake = _FakeEmbeddingService({"dairy": [1.0, 0.0, 0.0], "Milk drink": [1.0, 0.0, 0.0]})
    classifier = HybridCategoryClassifierService(
        embedding_service=fake, embedding_fallback=True, max_distance=0.45
    )
    product = _product("Milk drink «Some Brand» 1L")

    # when
    await classifier.classify_products([product], [dairy])

    # then
    assert product.get_category_uuid() == dairy.get_uuid()
