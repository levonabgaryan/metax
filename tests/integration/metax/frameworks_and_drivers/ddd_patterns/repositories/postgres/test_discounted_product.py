import datetime as dt
from decimal import Decimal
from uuid import uuid7

import pytest

from constants import ErrorCodes
from metax.core.application.ports.ddd_patterns.repository.entites_repositories.discounted_product import (
    DiscountedProductWithRelations,
)
from metax.core.application.ports.ddd_patterns.repository.errors import EntityIsNotFoundError
from metax.core.domain.entities.category.aggregate_root_entity import Category
from metax.core.domain.entities.category_helper_word.entity import CategoryHelperWord
from metax.core.domain.entities.discounted_product.aggregate_root_entity import (
    DiscountedProduct,
)
from metax.core.domain.entities.retailer.aggregate_root_entity import Retailer
from metax.core.domain.entities.retailer.value_objects import RetailersNames
from metax_lifespan import MetaxAppLifespanManager
from tests.utils import (
    make_category_entity,
    make_discounted_product_entity,
    make_helper_word_entity,
    make_retailer_entity,
)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_add_many_discounted_products(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work = metax_container_for_integration_tests.get_unit_of_work()

    created_data = dt.datetime.now(tz=dt.UTC)
    category_uuid = uuid7()
    helper_words = [
        CategoryHelperWord(
            uuid_=uuid7(),
            helper_word_text="օղի",
            created_at=created_data,
            updated_at=created_data,
        ),
        CategoryHelperWord(
            uuid_=uuid7(),
            helper_word_text="գինի",
            created_at=created_data,
            updated_at=created_data,
        ),
    ]
    category = Category(
        uuid_=category_uuid,
        name="Ալկոհոլ",
        helper_words=helper_words,
        created_at=created_data,
        updated_at=created_data,
    )

    sas_supermarket_uuid = uuid7()
    retailer = Retailer(
        uuid_=sas_supermarket_uuid,
        name=RetailersNames.SAS_AM,
        phone_number="test_phone_number",
        home_page_url="test_url",
        created_at=created_data,
        updated_at=created_data,
    )

    discounted_product_1_uuid = uuid7()
    absolut_vodka = DiscountedProduct(
        name="«Absolut» 0.7լ",
        category_uuid=category.get_uuid(),
        retailer_uuid=retailer.get_uuid(),
        url="test_url_1",
        real_price=Decimal("8390.00"),
        discounted_price=Decimal("7500.00"),
        uuid_=discounted_product_1_uuid,
        created_at=created_data,
        updated_at=created_data,
    )

    discounted_product_2_uuid = uuid7()
    karas_whine = DiscountedProduct(
        name="Փրփրուն գինի «Կարաս» 0.75լ",
        category_uuid=category.get_uuid(),
        retailer_uuid=retailer.get_uuid(),
        url="test_url_2",
        real_price=Decimal("5680.00"),
        discounted_price=Decimal("4950.00"),
        uuid_=discounted_product_2_uuid,
        created_at=created_data,
        updated_at=created_data,
    )

    discounted_products = [absolut_vodka, karas_whine]

    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.retailer_repo.add(retailer)
        await uow.commit()

    # when
    async with unit_of_work as uow:
        await uow.discounted_product_repo.add_many(discounted_products)
        await uow.commit()

    # then
    async with unit_of_work as uow:
        added_absolut_vodka = await uow.discounted_product_repo.get_by_uuid(discounted_product_1_uuid)
        added_karas_whine = await uow.discounted_product_repo.get_by_uuid(discounted_product_2_uuid)
        await uow.commit()

    assert added_absolut_vodka.get_uuid() == discounted_product_1_uuid
    assert added_absolut_vodka.get_name() == "«Absolut» 0.7լ"
    assert added_absolut_vodka.get_real_price() == Decimal("8390.00")
    assert added_absolut_vodka.get_discounted_price() == Decimal("7500.00")
    assert added_absolut_vodka.get_category_uuid() == category_uuid
    assert added_absolut_vodka.get_retailer_uuid() == sas_supermarket_uuid
    assert added_absolut_vodka.get_url() == "test_url_1"

    assert added_karas_whine.get_uuid() == discounted_product_2_uuid
    assert added_karas_whine.get_name() == "Փրփրուն գինի «Կարաս» 0.75լ"
    assert added_karas_whine.get_real_price() == Decimal("5680.00")
    assert added_karas_whine.get_discounted_price() == Decimal("4950.00")
    assert added_karas_whine.get_category_uuid() == category_uuid
    assert added_karas_whine.get_retailer_uuid() == sas_supermarket_uuid
    assert added_karas_whine.get_url() == "test_url_2"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_discounted_products_is_not_found_by_uuid(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work = metax_container_for_integration_tests.get_unit_of_work()

    random_uuid = uuid7()
    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError) as err:
            await uow.discounted_product_repo.get_by_uuid(random_uuid)

    # then
    assert err.value.title == "discounted_product not found."
    assert err.value.details == f"No discounted_product found by 'uuid' = '{random_uuid}'."
    assert err.value.error_code == ErrorCodes.ENTITY_IS_NOT_FOUND


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_delete_older_than_and_return_deleted_count(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work = metax_container_for_integration_tests.get_unit_of_work()

    creation_date = dt.datetime.now(tz=dt.UTC)
    retailer = make_retailer_entity()
    discounted_product = make_discounted_product_entity(
        created_at=creation_date, retailer_uuid=retailer.get_uuid()
    )

    async with unit_of_work as uow:
        await uow.retailer_repo.add(retailer)
        await uow.discounted_product_repo.add_many([discounted_product])
        await uow.commit()

    # when
    async with unit_of_work as uow:
        deleted_count = await uow.discounted_product_repo.delete_older_than_and_return_deleted_count(
            date_limit=creation_date + dt.timedelta(hours=1)
        )
        await uow.commit()

    # then
    assert deleted_count == 1
    all_products = [product async for product in uow.discounted_product_repo.all()]
    assert len(all_products) == 0


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_delete_category_by_uuid_sets_category_to_null_for_matching_products(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work = metax_container_for_integration_tests.get_unit_of_work()
    created_at = dt.datetime.now(tz=dt.UTC)
    retailer = make_retailer_entity()
    helper_word_1 = make_helper_word_entity(
        helper_word_text="Helper word 1",
    )
    helper_word_2 = make_helper_word_entity(
        helper_word_text="Helper word 2",
    )
    target_category = make_category_entity(name="TargetCategory", helper_words=[helper_word_1])
    other_category = make_category_entity(name="OtherCategory", helper_words=[helper_word_2])

    target_product_1 = make_discounted_product_entity(
        retailer_uuid=retailer.get_uuid(),
        category_uuid=target_category.get_uuid(),
        created_at=created_at,
        name="target_1",
    )
    target_product_2 = make_discounted_product_entity(
        retailer_uuid=retailer.get_uuid(),
        category_uuid=target_category.get_uuid(),
        created_at=created_at,
        name="target_2",
    )
    other_category_product = make_discounted_product_entity(
        retailer_uuid=retailer.get_uuid(),
        category_uuid=other_category.get_uuid(),
        created_at=created_at,
        name="other_category_product",
    )
    no_category_product = make_discounted_product_entity(
        retailer_uuid=retailer.get_uuid(),
        created_at=created_at,
        name="no_category_product",
    )
    async with unit_of_work as uow:
        await uow.retailer_repo.add(retailer)
        await uow.category_repo.add(target_category)
        await uow.category_repo.add(other_category)
        await uow.discounted_product_repo.add_many([
            target_product_1,
            target_product_2,
            other_category_product,
            no_category_product,
        ])
        await uow.commit()

    # when
    async with unit_of_work as uow:
        updated_count = await uow.discounted_product_repo.delete_category_by_uuid(target_category.get_uuid())
        await uow.commit()

    # then
    assert updated_count == 2
    async with unit_of_work as uow:
        loaded_target_product_1 = await uow.discounted_product_repo.get_by_uuid(target_product_1.get_uuid())
        loaded_target_product_2 = await uow.discounted_product_repo.get_by_uuid(target_product_2.get_uuid())
        loaded_other_category_product = await uow.discounted_product_repo.get_by_uuid(
            other_category_product.get_uuid()
        )
        loaded_no_category_product = await uow.discounted_product_repo.get_by_uuid(no_category_product.get_uuid())

    assert not loaded_target_product_1.has_category()
    assert not loaded_target_product_2.has_category()
    assert loaded_other_category_product.get_category_uuid() == other_category.get_uuid()
    assert not loaded_no_category_product.has_category()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_get_all_when_no_discounted_products(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work = metax_container_for_integration_tests.get_unit_of_work()

    # when
    async with unit_of_work as uow:
        products = [p async for p in uow.discounted_product_repo.all()]

    # then
    assert products == []


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_get_all_returns_all_products_ordered_by_uuid(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work = metax_container_for_integration_tests.get_unit_of_work()
    created_at = dt.datetime(2026, 6, 15, 12, 0, 0, tzinfo=dt.UTC)
    retailer = make_retailer_entity()
    category = make_category_entity(name="CategoryForGetAll")
    uuid_high = uuid7()
    uuid_mid = uuid7()
    uuid_low = uuid7()
    ordered_uuids = sorted([uuid_low, uuid_mid, uuid_high], key=lambda u: u.bytes)
    p_low = make_discounted_product_entity(
        retailer_uuid=retailer.get_uuid(),
        category_uuid=category.get_uuid(),
        created_at=created_at,
        discounted_product_uuid=ordered_uuids[0],
        name="low",
    )
    p_mid = make_discounted_product_entity(
        retailer_uuid=retailer.get_uuid(),
        category_uuid=category.get_uuid(),
        created_at=created_at,
        discounted_product_uuid=ordered_uuids[1],
        name="mid",
    )
    p_high = make_discounted_product_entity(
        retailer_uuid=retailer.get_uuid(),
        category_uuid=category.get_uuid(),
        created_at=created_at,
        discounted_product_uuid=ordered_uuids[2],
        name="high",
    )

    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.retailer_repo.add(retailer)
        await uow.discounted_product_repo.add_many([p_mid, p_high, p_low])
        await uow.commit()

    # when
    async with unit_of_work as uow:
        loaded = [p async for p in uow.discounted_product_repo.all()]

    # then
    assert [p.get_uuid() for p in loaded] == ordered_uuids
    assert {p.get_name() for p in loaded} == {"low", "mid", "high"}
    for p in loaded:
        assert p.get_retailer_uuid() == retailer.get_uuid()
        assert p.get_category_uuid() == category.get_uuid()
        assert p.get_created_at() == created_at


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_get_all_chunk_size(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work = metax_container_for_integration_tests.get_unit_of_work()
    created_at = dt.datetime(2026, 7, 1, 8, 0, 0, tzinfo=dt.UTC)
    retailer = make_retailer_entity()
    uuids = sorted([uuid7() for _ in range(5)], key=lambda u: u.bytes)
    products = [
        make_discounted_product_entity(
            retailer_uuid=retailer.get_uuid(),
            created_at=created_at,
            discounted_product_uuid=u,
            name=f"p{i}",
        )
        for i, u in enumerate(uuids)
    ]

    async with unit_of_work as uow:
        await uow.retailer_repo.add(retailer)
        await uow.discounted_product_repo.add_many(products)
        await uow.commit()

    # when
    async with unit_of_work as uow:
        loaded = [p async for p in uow.discounted_product_repo.all(chunk_size=2)]

    # then
    assert {p.get_uuid() for p in loaded} == set(uuids)
    assert len(loaded) == 5


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_get_by_created_at_returns_empty_when_no_rows_for_date(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work = metax_container_for_integration_tests.get_unit_of_work()
    query_date = dt.datetime(2026, 8, 1, 0, 0, 0, tzinfo=dt.UTC)

    # when
    async with unit_of_work as uow:
        rows = [r async for r in uow.discounted_product_repo.get_by_created_at(created_at=query_date)]

    # then
    assert rows == []


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_get_by_created_at(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work = metax_container_for_integration_tests.get_unit_of_work()
    created_at = dt.datetime(2026, 9, 10, 15, 30, 0, tzinfo=dt.UTC)
    category = make_category_entity(name="JoinedCategoryName")
    retailer = make_retailer_entity()
    p1 = make_discounted_product_entity(
        retailer_uuid=retailer.get_uuid(),
        category_uuid=category.get_uuid(),
        created_at=created_at,
        name="one",
    )
    p2 = make_discounted_product_entity(
        retailer_uuid=retailer.get_uuid(),
        category_uuid=category.get_uuid(),
        created_at=created_at,
        name="two",
    )

    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.retailer_repo.add(retailer)
        await uow.discounted_product_repo.add_many([p1, p2])
        await uow.commit()

    # when
    async with unit_of_work as uow:
        rows: list[DiscountedProductWithRelations] = [
            r async for r in uow.discounted_product_repo.get_by_created_at(created_at=created_at)
        ]

    # then
    assert len(rows) == 2
    for row in rows:
        assert row.category is not None
        assert row.category.get_name() == "JoinedCategoryName"
        assert row.category.get_uuid() == category.get_uuid()
        assert row.retailer.get_name() == str(retailer.get_name())
        assert row.retailer.get_home_page_url() == retailer.get_home_page_url()
        assert row.retailer.get_phone_number() == retailer.get_phone_number()
        assert row.retailer.get_uuid() == retailer.get_uuid()
        assert row.entity.get_created_at() == created_at
        assert row.entity.get_retailer_uuid() == retailer.get_uuid()
        assert row.entity.get_category_uuid() == category.get_uuid()
    assert {row.entity.get_name() for row in rows} == {"one", "two"}


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_get_by_created_at_filters_by_created_at(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work = metax_container_for_integration_tests.get_unit_of_work()
    date_a = dt.datetime(2026, 10, 1, 10, 0, 0, tzinfo=dt.UTC)
    date_b = dt.datetime(2026, 10, 2, 10, 0, 0, tzinfo=dt.UTC)
    retailer = make_retailer_entity()
    product_a = make_discounted_product_entity(retailer_uuid=retailer.get_uuid(), created_at=date_a, name="on_a")
    product_b = make_discounted_product_entity(retailer_uuid=retailer.get_uuid(), created_at=date_b, name="on_b")

    async with unit_of_work as uow:
        await uow.retailer_repo.add(retailer)
        await uow.discounted_product_repo.add_many([product_a, product_b])
        await uow.commit()

    # when
    async with unit_of_work as uow:
        rows_a = [r async for r in uow.discounted_product_repo.get_by_created_at(created_at=date_a)]
        rows_b = [r async for r in uow.discounted_product_repo.get_by_created_at(created_at=date_b)]

    # then
    assert len(rows_a) == 1
    assert rows_a[0].entity.get_name() == "on_a"
    assert len(rows_b) == 1
    assert rows_b[0].entity.get_name() == "on_b"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_get_by_created_at_without_category_returns_none_category_name(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work = metax_container_for_integration_tests.get_unit_of_work()
    created_at = dt.datetime(2026, 11, 5, 12, 0, 0, tzinfo=dt.UTC)
    retailer = make_retailer_entity()
    product = make_discounted_product_entity(retailer_uuid=retailer.get_uuid(), created_at=created_at)

    async with unit_of_work as uow:
        await uow.retailer_repo.add(retailer)
        await uow.discounted_product_repo.add_many([product])
        await uow.commit()

    # when
    async with unit_of_work as uow:
        rows = [r async for r in uow.discounted_product_repo.get_by_created_at(created_at=created_at)]

    # then
    assert len(rows) == 1
    assert rows[0].category is None
    assert not rows[0].entity.has_category()
    assert rows[0].retailer.get_name() == str(retailer.get_name())


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_by_created_at_chunk_size(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work = metax_container_for_integration_tests.get_unit_of_work()
    created_at = dt.datetime(2026, 12, 1, 0, 0, 0, tzinfo=dt.UTC)
    retailer = make_retailer_entity()
    products = [
        make_discounted_product_entity(
            retailer_uuid=retailer.get_uuid(),
            created_at=created_at,
            name=f"c{i}",
        )
        for i in range(5)
    ]

    async with unit_of_work as uow:
        await uow.retailer_repo.add(retailer)
        await uow.discounted_product_repo.add_many(products)
        await uow.commit()

    # when
    async with unit_of_work as uow:
        rows = [
            r async for r in uow.discounted_product_repo.get_by_created_at(created_at=created_at, chunk_size=2)
        ]

    # then
    assert len(rows) == 5
    assert {r.entity.get_name() for r in rows} == {f"c{i}" for i in range(5)}
