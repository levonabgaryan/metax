import uuid
from datetime import UTC, datetime, timedelta

import pytest

from metax.core.application.read_models.discounted_product import (
    DiscountedProductCategoryReadModel,
    DiscountedProductRetailerReadModel,
)
from metax.core.domain.entities.retailer.value_objects import RetailersNames
from metax.frameworks_and_drivers.opensearch.indices import discounted_product_read_model
from metax_lifespan import MetaxAppLifespanManager
from tests.integration.conftest import refresh_opensearch_index
from tests.utils import (
    make_category_entity,
    make_discounted_product_read_model,
    make_retailer_entity,
)


@pytest.mark.asyncio
async def test_delete_older_than_and_return_deleted_count(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_integration_tests.get_di_container()
    repos = metax_container_for_integration_tests.repositories_container.container
    repo = await repos.discounted_product_read_model_repository.async_()
    creation_date = datetime.now(tz=UTC)

    discounted_products_read_models = [
        make_discounted_product_read_model(
            created_at=creation_date,
            name=f"test_product_name{i}",
            retailer_name=RetailersNames.YEREVAN_CITY.value,
            discounted_product_uuid=str(uuid.uuid7()),
        )
        for i in range(5)
    ]

    await repo.add_many(discounted_products_read_models)

    await refresh_opensearch_index(
        metax_lifespan_manager_for_integration_tests, discounted_product_read_model.ALIAS_NAME
    )

    # when
    deleted_count = await repo.delete_older_than_and_return_deleted_count(
        date_limit=creation_date + timedelta(days=1)
    )
    await refresh_opensearch_index(
        metax_lifespan_manager_for_integration_tests, discounted_product_read_model.ALIAS_NAME
    )

    # then
    assert deleted_count == 5
    assert await repo.get_all_count() == 0


@pytest.mark.asyncio
async def test_update_category(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_integration_tests.get_di_container()
    repos = metax_container_for_integration_tests.repositories_container.container
    repo = await repos.discounted_product_read_model_repository.async_()
    created_at = datetime.now(tz=UTC)
    category = make_category_entity()
    discounted_product_read_model_ = make_discounted_product_read_model(
        created_at=created_at,
        discounted_product_uuid=str(uuid.uuid7()),
        category_name=category.get_name(),
        category_uuid=str(category.get_uuid()),
    )

    await repo.add_many([discounted_product_read_model_])
    await refresh_opensearch_index(
        metax_lifespan_manager_for_integration_tests, discounted_product_read_model.ALIAS_NAME
    )

    # when
    category.set_name("category_new_name")
    await repo.update_categories(
        DiscountedProductCategoryReadModel(
            uuid_=str(category.get_uuid()),
            created_at=category.get_created_at().isoformat(),
            updated_at=category.get_updated_at().isoformat(),
            name=category.get_name(),
        ),
    )
    await refresh_opensearch_index(
        metax_lifespan_manager_for_integration_tests, discounted_product_read_model.ALIAS_NAME
    )

    # then
    updated_discounted_product_read_model = await repo.get_by_uuid(uuid_=discounted_product_read_model_["uuid_"])
    assert updated_discounted_product_read_model["category"]["name"] == "category_new_name"


@pytest.mark.asyncio
async def test_update_retailer(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_integration_tests.get_di_container()
    repos = metax_container_for_integration_tests.repositories_container.container
    repo = await repos.discounted_product_read_model_repository.async_()
    retailer = make_retailer_entity()
    created_at = datetime.now(tz=UTC)
    discounted_product_read_model_ = make_discounted_product_read_model(
        created_at=created_at,
        discounted_product_uuid=str(uuid.uuid7()),
        retailer_uuid=str(retailer.get_uuid()),
        retailer_name=retailer.get_name(),
    )
    await repo.add_many([discounted_product_read_model_])
    await refresh_opensearch_index(
        metax_lifespan_manager_for_integration_tests, discounted_product_read_model.ALIAS_NAME
    )

    # when
    retailer.set_name(RetailersNames.SAS_AM.value)
    retailer.set_home_page_url("new_url")
    retailer.set_phone_number("new_phone_number")
    await repo.update_retailers(
        DiscountedProductRetailerReadModel(
            uuid_=str(retailer.get_uuid()),
            created_at=retailer.get_created_at().isoformat(),
            updated_at=retailer.get_updated_at().isoformat(),
            name=retailer.get_name(),
            home_page_url=retailer.get_home_page_url(),
            phone_number=retailer.get_phone_number(),
        ),
    )
    await refresh_opensearch_index(
        metax_lifespan_manager_for_integration_tests, discounted_product_read_model.ALIAS_NAME
    )

    # then
    updated_discounted_product_read_model = await repo.get_by_uuid(uuid_=discounted_product_read_model_["uuid_"])
    assert updated_discounted_product_read_model["retailer"]["name"] == RetailersNames.SAS_AM.value
    assert updated_discounted_product_read_model["retailer"]["home_page_url"] == "new_url"
    assert updated_discounted_product_read_model["retailer"]["phone_number"] == "new_phone_number"


@pytest.mark.asyncio
async def test_get_all(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_integration_tests.get_di_container()
    repos = metax_container_for_integration_tests.repositories_container.container
    repo = await repos.discounted_product_read_model_repository.async_()
    created_at = datetime.now(tz=UTC)
    discounted_product_read_models = [
        make_discounted_product_read_model(
            created_at=created_at,
            discounted_product_uuid=str(uuid.uuid7()),
        )
        for _ in range(5)
    ]
    await repo.add_many(discounted_product_read_models)
    await refresh_opensearch_index(
        metax_lifespan_manager_for_integration_tests, discounted_product_read_model.ALIAS_NAME
    )

    # when
    got_discounted_product_read_models = repo.all()

    # then
    async for product in got_discounted_product_read_models:
        assert product["uuid_"] in {given_product["uuid_"] for given_product in discounted_product_read_models}
        assert product["name"] in {given_product["name"] for given_product in discounted_product_read_models}
        assert product["real_price"] in {
            given_product["real_price"] for given_product in discounted_product_read_models
        }
        assert product["discounted_price"] in {
            given_product["discounted_price"] for given_product in discounted_product_read_models
        }


@pytest.mark.asyncio
@pytest.mark.parametrize("query", ["gi", "gini", "գի", "գինի", "Blue Nun", "Gold Edition"])
async def test_search_by_name_two_pages(
    query: str,
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given — two products that should both match the same full-text query; others do not.
    metax_container_for_integration_tests = metax_lifespan_manager_for_integration_tests.get_di_container()
    repos = metax_container_for_integration_tests.repositories_container.container
    repo = await repos.discounted_product_read_model_repository.async_()
    created_at = datetime.now(tz=UTC)
    wine_gold = make_discounted_product_read_model(
        created_at=created_at,
        discounted_product_uuid=str(uuid.uuid7()),
        name="Փրփրուն գինի «Blue Nun Gold Edition» 0.75լ",
    )
    wine_extra = make_discounted_product_read_model(
        created_at=created_at,
        discounted_product_uuid=str(uuid.uuid7()),
        name="Գինի «Blue Nun Gold Edition» 0.5լ — երկրորդ տարաձև",
    )
    noise_products = [
        make_discounted_product_read_model(
            created_at=created_at,
            discounted_product_uuid=str(uuid.uuid7()),
        )
        for _ in range(15)
    ]
    await repo.add_many([*noise_products, wine_gold, wine_extra])
    await refresh_opensearch_index(
        metax_lifespan_manager_for_integration_tests, discounted_product_read_model.ALIAS_NAME
    )
    expected_uuids = {wine_gold["uuid_"], wine_extra["uuid_"]}
    expected_by_uuid = {wine_gold["uuid_"]: wine_gold, wine_extra["uuid_"]: wine_extra}

    # when / then — first page
    page1, total_first = await repo.search_by_name(name=query, offset=0, limit=1)
    assert total_first == 2
    assert len(page1) == 1
    assert page1[0]["uuid_"] in expected_uuids
    assert page1[0]["name"] == expected_by_uuid[page1[0]["uuid_"]]["name"]

    # second page (same total; different hit than page 1)
    page2, total_second = await repo.search_by_name(name=query, offset=1, limit=1)
    assert total_second == 2
    assert len(page2) == 1
    assert page2[0]["uuid_"] in expected_uuids
    assert page2[0]["name"] == expected_by_uuid[page2[0]["uuid_"]]["name"]
    assert page1[0]["uuid_"] != page2[0]["uuid_"]

    assert {page1[0]["uuid_"], page2[0]["uuid_"]} == expected_uuids
