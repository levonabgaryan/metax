"""Integration tests for the pgvector-backed discounted-product search read model.

These exercise the real embedding service (armenian-text-embeddings-2-large), so they
require the metax-embeddings container from the test stack to be up with the model loaded.
"""

import datetime as dt
from decimal import Decimal

import pytest

from metax_lifespan import MetaxAppLifespanManager
from tests.utils import (
    make_category_entity,
    make_discounted_product_entity,
    make_retailer_entity,
)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_embed_pending_then_search_by_name_floats_exact_match_first(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    container = metax_lifespan_manager_for_tests.get_metax_container()
    uow = container.get_unit_of_work()
    read_repo = await container.get_discounted_product_read_model_repository()
    created_at = dt.datetime.now(tz=dt.UTC)

    retailer = make_retailer_entity()
    lays = make_discounted_product_entity(
        retailer_uuid=retailer.get_uuid(), created_at=created_at, name="lays chips 100g"
    )
    cola = make_discounted_product_entity(
        retailer_uuid=retailer.get_uuid(), created_at=created_at, name="coca cola 1.5L"
    )
    async with uow as u:
        await u.retailer_repo.add(retailer)
        await u.discounted_product_repo.add_many([lays, cola])
        await u.commit()

    # when
    embedded_count = await read_repo.embed_pending()
    items, total = await read_repo.search_by_name("lays", limit=10)

    # then
    assert embedded_count == 2
    assert total >= 1
    assert items[0]["name"] == "lays chips 100g"
    assert items[0]["retailer"]["uuid_"] == str(retailer.get_uuid())


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_search_by_name_and_by_retailer_uuid_filters_to_one_retailer(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    container = metax_lifespan_manager_for_tests.get_metax_container()
    uow = container.get_unit_of_work()
    read_repo = await container.get_discounted_product_read_model_repository()
    created_at = dt.datetime.now(tz=dt.UTC)

    retailer_a = make_retailer_entity(name="sas-am")
    retailer_b = make_retailer_entity(name="yerevan-city")
    product_a = make_discounted_product_entity(
        retailer_uuid=retailer_a.get_uuid(), created_at=created_at, name="lays chips a"
    )
    product_b = make_discounted_product_entity(
        retailer_uuid=retailer_b.get_uuid(), created_at=created_at, name="lays chips b"
    )
    async with uow as u:
        await u.retailer_repo.add(retailer_a)
        await u.retailer_repo.add(retailer_b)
        await u.discounted_product_repo.add_many([product_a, product_b])
        await u.commit()
    await read_repo.embed_pending()

    # when
    items, total = await read_repo.search_by_name_and_by_retailer_uuid(
        "lays", retailer_uuid=str(retailer_a.get_uuid()), limit=10
    )

    # then
    assert total == 1
    assert items[0]["retailer"]["uuid_"] == str(retailer_a.get_uuid())


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_search_by_category_uuid_orders_by_discounted_price(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    container = metax_lifespan_manager_for_tests.get_metax_container()
    uow = container.get_unit_of_work()
    read_repo = await container.get_discounted_product_read_model_repository()
    created_at = dt.datetime.now(tz=dt.UTC)

    retailer = make_retailer_entity()
    category = make_category_entity()
    cheap = make_discounted_product_entity(
        retailer_uuid=retailer.get_uuid(),
        category_uuid=category.get_uuid(),
        created_at=created_at,
        name="cheap product",
        real_price=Decimal(1000),
        discounted_price=Decimal(100),
    )
    pricey = make_discounted_product_entity(
        retailer_uuid=retailer.get_uuid(),
        category_uuid=category.get_uuid(),
        created_at=created_at,
        name="pricey product",
        real_price=Decimal(1000),
        discounted_price=Decimal(900),
    )
    async with uow as u:
        await u.retailer_repo.add(retailer)
        await u.category_repo.add(category)
        await u.discounted_product_repo.add_many([pricey, cheap])
        await u.commit()

    # when (no embedding needed for a pure category listing)
    items, total = await read_repo.search_by_category_uuid(str(category.get_uuid()), limit=10)

    # then
    assert total == 2
    assert [item["name"] for item in items] == ["cheap product", "pricey product"]
    assert items[0]["category"]["uuid_"] == str(category.get_uuid())


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_get_by_uuid_returns_full_read_model(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    container = metax_lifespan_manager_for_tests.get_metax_container()
    uow = container.get_unit_of_work()
    read_repo = await container.get_discounted_product_read_model_repository()
    created_at = dt.datetime.now(tz=dt.UTC)

    retailer = make_retailer_entity()
    product = make_discounted_product_entity(
        retailer_uuid=retailer.get_uuid(), created_at=created_at, name="single product"
    )
    async with uow as u:
        await u.retailer_repo.add(retailer)
        await u.discounted_product_repo.add_many([product])
        await u.commit()

    # when
    read_model = await read_repo.get_by_uuid(str(product.get_uuid()))

    # then
    assert read_model["uuid_"] == str(product.get_uuid())
    assert read_model["name"] == "single product"
    assert read_model["retailer"]["uuid_"] == str(retailer.get_uuid())
    assert "category" not in read_model


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_search_matches_latin_transliteration_of_armenian_name(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given: an Armenian-named product ("կարագ" = butter), embedded so it is searchable
    container = metax_lifespan_manager_for_tests.get_metax_container()
    uow = container.get_unit_of_work()
    read_repo = await container.get_discounted_product_read_model_repository()
    created_at = dt.datetime.now(tz=dt.UTC)

    retailer = make_retailer_entity()
    butter = make_discounted_product_entity(
        retailer_uuid=retailer.get_uuid(), created_at=created_at, name="կարագ"
    )
    async with uow as u:
        await u.retailer_repo.add(retailer)
        await u.discounted_product_repo.add_many([butter])
        await u.commit()
    await read_repo.embed_pending()

    # when: the user types the Latin phonetic form
    items, total = await read_repo.search_by_name("karag", limit=10)

    # then: the Armenian product is found via the transliterated name
    assert total >= 1
    assert any(item["uuid_"] == str(butter.get_uuid()) for item in items)
