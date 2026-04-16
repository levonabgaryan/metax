import uuid
from datetime import datetime, timedelta, timezone

import pytest

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
    metax_app_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_app_for_integration_tests.get_di_container()
    repos = metax_container_for_integration_tests.repositories_container.container
    repo = await repos.discounted_product_read_model_repository.async_()
    creation_date = datetime.now(tz=timezone.utc)

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

    await refresh_opensearch_index(metax_app_for_integration_tests, discounted_product_read_model.ALIAS_NAME)

    # when
    deleted_count = await repo.delete_older_than_and_return_deleted_count(
        date_limit=creation_date + timedelta(days=1)
    )
    await refresh_opensearch_index(metax_app_for_integration_tests, discounted_product_read_model.ALIAS_NAME)

    # then
    assert deleted_count == 5
    assert await repo.get_all_count() == 0


@pytest.mark.asyncio
async def test_update_category(
    metax_app_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_app_for_integration_tests.get_di_container()
    repos = metax_container_for_integration_tests.repositories_container.container
    repo = await repos.discounted_product_read_model_repository.async_()
    created_at = datetime.now(tz=timezone.utc)
    category = make_category_entity()
    discounted_product_read_model_ = make_discounted_product_read_model(
        created_at=created_at,
        discounted_product_uuid=str(uuid.uuid7()),
        category_name=category.get_name(),
        category_uuid=str(category.get_uuid()),
    )

    await repo.add_many([discounted_product_read_model_])
    await refresh_opensearch_index(metax_app_for_integration_tests, discounted_product_read_model.ALIAS_NAME)

    # when
    category.set_name("category_new_name")
    await repo.update_category_names_by_category_uuid(
        category_uuid=str(category.get_uuid()),
        new_category_name=category.get_name(),
    )
    await refresh_opensearch_index(metax_app_for_integration_tests, discounted_product_read_model.ALIAS_NAME)

    # then
    updated_discounted_product_read_model = await repo.get_by_uuid(uuid_=discounted_product_read_model_["uuid_"])
    assert updated_discounted_product_read_model["category_name"] == "category_new_name"


@pytest.mark.asyncio
async def test_update_retailer(
    metax_app_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_app_for_integration_tests.get_di_container()
    repos = metax_container_for_integration_tests.repositories_container.container
    repo = await repos.discounted_product_read_model_repository.async_()
    retailer = make_retailer_entity()
    created_at = datetime.now(tz=timezone.utc)
    discounted_product_read_model_ = make_discounted_product_read_model(
        created_at=created_at,
        discounted_product_uuid=str(uuid.uuid7()),
        retailer_uuid=str(retailer.get_uuid()),
        retailer_name=retailer.get_name(),
    )
    await repo.add_many([discounted_product_read_model_])
    await refresh_opensearch_index(metax_app_for_integration_tests, discounted_product_read_model.ALIAS_NAME)

    # when
    retailer.set_name(RetailersNames.SAS_AM.value)
    retailer.set_home_page_url("new_url")
    retailer.set_phone_number("new_phone_number")
    await repo.update_retailer_names_by_retailer_uuid(
        retailer_uuid=str(retailer.get_uuid()),
        new_retailer_name=retailer.get_name(),
    )
    await refresh_opensearch_index(metax_app_for_integration_tests, discounted_product_read_model.ALIAS_NAME)

    # then
    updated_discounted_product_read_model = await repo.get_by_uuid(uuid_=discounted_product_read_model_["uuid_"])
    assert updated_discounted_product_read_model["retailer_name"] == RetailersNames.SAS_AM.value


@pytest.mark.asyncio
async def test_get_all(
    metax_app_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_app_for_integration_tests.get_di_container()
    repos = metax_container_for_integration_tests.repositories_container.container
    repo = await repos.discounted_product_read_model_repository.async_()
    created_at = datetime.now(tz=timezone.utc)
    discounted_product_read_models = [
        make_discounted_product_read_model(
            created_at=created_at,
            discounted_product_uuid=str(uuid.uuid7()),
        )
        for _ in range(5)
    ]
    await repo.add_many(discounted_product_read_models)
    await refresh_opensearch_index(metax_app_for_integration_tests, discounted_product_read_model.ALIAS_NAME)

    # when
    got_discounted_product_read_models = repo.get_all()

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
async def test_get_by_name_page(
    query: str,
    metax_app_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_app_for_integration_tests.get_di_container()
    repos = metax_container_for_integration_tests.repositories_container.container
    repo = await repos.discounted_product_read_model_repository.async_()
    created_at = datetime.now(tz=timezone.utc)
    discounted_product_read_model_ = make_discounted_product_read_model(
        created_at=created_at,
        discounted_product_uuid=str(uuid.uuid7()),
        name="Փրփրուն գինի «Blue Nun Gold Edition» 0.75լ",
    )
    discounted_product_read_models = [
        make_discounted_product_read_model(
            created_at=created_at,
            discounted_product_uuid=str(uuid.uuid7()),
        )
        for _ in range(15)
    ]
    discounted_product_read_models.append(discounted_product_read_model_)
    await repo.add_many(discounted_product_read_models)
    await refresh_opensearch_index(metax_app_for_integration_tests, discounted_product_read_model.ALIAS_NAME)

    # when
    found_products, scroll_id = await repo.get_by_name_page(name=query, chunk_size=1)

    # then
    # first_page
    assert scroll_id is not None
    assert len(found_products) == 1
    found_product = found_products[0]
    assert found_product["uuid_"] == discounted_product_read_model_["uuid_"]
    assert found_product["name"] == discounted_product_read_model_["name"]

    # second page
    found_products, scroll_id = await repo.get_by_name_page(name=query, cursor_=scroll_id)
    assert scroll_id is None
    assert len(found_products) == 0
