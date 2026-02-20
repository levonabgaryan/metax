import uuid
from datetime import datetime, timezone, timedelta

import pytest

from discount_service.core.domain.entities.category_entity.category import DataForCategoryUpdate
from discount_service.core.domain.entities.retailer_entity.retailer import DataForRetailerUpdate
from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer

from tests.utils import (
    clear_opensearch_db,
    make_discounted_product_read_model,
    make_category_entity,
    make_retailer_entity,
)
from tests.integration.conftest import refresh_opensearch_index
from discount_service.frameworks_and_drivers.opensearch.indices import discounted_product_read_model


@pytest.mark.asyncio
@clear_opensearch_db
async def test_delete_older_than_and_return_deleted_count(
    service_container_for_tests: ServiceContainer,
) -> None:
    # given
    unit_of_work = await service_container_for_tests.patterns_container.container.unit_of_work.async_()

    creation_date = datetime.now(tz=timezone.utc)

    discounted_products_read_models = [
        make_discounted_product_read_model(
            created_at=creation_date,
            name=f"test_product_name{i}",
            retailer_name=f"test_retailer{i}",
            discounted_product_uuid=str(uuid.uuid4()),
        )
        for i in range(5)
    ]

    repo = unit_of_work.discounted_product_read_model_repo
    await repo.add_many(discounted_products_read_models)

    await refresh_opensearch_index(index_or_alias_name=discounted_product_read_model.ALIAS_NAME)

    # when
    deleted_count = await repo.delete_older_than_and_return_deleted_count(
        date_limit=creation_date + timedelta(days=1)
    )
    await refresh_opensearch_index(index_or_alias_name=discounted_product_read_model.ALIAS_NAME)

    # then
    assert deleted_count == 5
    assert await repo.get_all_count() == 0


@pytest.mark.asyncio
@clear_opensearch_db
async def test_update_category(service_container_for_tests: ServiceContainer) -> None:
    # given
    unit_of_work = await service_container_for_tests.patterns_container.container.unit_of_work.async_()

    created_at = datetime.now(tz=timezone.utc)
    category = make_category_entity()
    discounted_product_read_model_ = make_discounted_product_read_model(
        created_at=created_at,
        discounted_product_uuid=str(uuid.uuid4()),
        category_name=category.get_name(),
        category_uuid=str(category.get_uuid()),
    )

    repo = unit_of_work.discounted_product_read_model_repo
    await repo.add_many([discounted_product_read_model_])
    await refresh_opensearch_index(index_or_alias_name=discounted_product_read_model.ALIAS_NAME)

    # when
    data_for_update = DataForCategoryUpdate(new_name="category_new_name")
    category.update(new_data=data_for_update)
    await repo.update_category(updated_category=category)
    await refresh_opensearch_index(index_or_alias_name=discounted_product_read_model.ALIAS_NAME)

    # then
    updated_discounted_product_read_model = await repo.get_by_uuid(
        discounted_product_read_model_uuid=discounted_product_read_model_["discounted_product_uuid"]
    )
    assert updated_discounted_product_read_model["category_name"] == "category_new_name"


@pytest.mark.asyncio
@clear_opensearch_db
async def test_update_retailer(service_container_for_tests: ServiceContainer) -> None:
    # given
    unit_of_work = await service_container_for_tests.patterns_container.container.unit_of_work.async_()

    retailer = make_retailer_entity()
    created_at = datetime.now(tz=timezone.utc)
    discounted_product_read_model_ = make_discounted_product_read_model(
        created_at=created_at,
        discounted_product_uuid=str(uuid.uuid4()),
        retailer_uuid=str(retailer.get_uuid()),
        retailer_name=retailer.get_name(),
    )
    repo = unit_of_work.discounted_product_read_model_repo
    await repo.add_many([discounted_product_read_model_])
    await refresh_opensearch_index(index_or_alias_name=discounted_product_read_model.ALIAS_NAME)

    # when
    data_for_update = DataForRetailerUpdate(
        new_name="retailer_new_name",
        new_url="new_url",
        new_phone_number="new_phone_number",
    )
    retailer.update(new_data=data_for_update)
    await repo.update_retailer(updated_retailer=retailer)
    await refresh_opensearch_index(index_or_alias_name=discounted_product_read_model.ALIAS_NAME)

    # then
    updated_discounted_product_read_model = await repo.get_by_uuid(
        discounted_product_read_model_uuid=discounted_product_read_model_["discounted_product_uuid"]
    )
    assert updated_discounted_product_read_model["retailer_name"] == "retailer_new_name"


@pytest.mark.asyncio
@clear_opensearch_db
async def test_get_all(service_container_for_tests: ServiceContainer) -> None:
    # given
    unit_of_work = await service_container_for_tests.patterns_container.container.unit_of_work.async_()

    created_at = datetime.now(tz=timezone.utc)
    discounted_product_read_models = [
        make_discounted_product_read_model(
            created_at=created_at,
            discounted_product_uuid=str(uuid.uuid4()),
        )
        for _ in range(5)
    ]
    repo = unit_of_work.discounted_product_read_model_repo
    await repo.add_many(discounted_product_read_models)
    await refresh_opensearch_index(index_or_alias_name=discounted_product_read_model.ALIAS_NAME)

    # when
    got_discounted_product_read_models = repo.get_all()

    # then
    async for product in got_discounted_product_read_models:
        assert product["discounted_product_uuid"] in {
            given_product["discounted_product_uuid"] for given_product in discounted_product_read_models
        }
        assert product["name"] in {given_product["name"] for given_product in discounted_product_read_models}
        assert product["real_price"] in {
            given_product["real_price"] for given_product in discounted_product_read_models
        }
        assert product["discounted_price"] in {
            given_product["discounted_price"] for given_product in discounted_product_read_models
        }


@pytest.mark.asyncio
@clear_opensearch_db
@pytest.mark.parametrize("query", ["gi", "gini", "գի", "գինի", "Blue Nun", "Gold Edition"])
async def test_get_by_name_page(query: str, service_container_for_tests: ServiceContainer) -> None:
    # given
    unit_of_work = await service_container_for_tests.patterns_container.container.unit_of_work.async_()

    created_at = datetime.now(tz=timezone.utc)
    discounted_product_read_model_ = make_discounted_product_read_model(
        created_at=created_at,
        discounted_product_uuid=str(uuid.uuid4()),
        name="Փրփրուն գինի «Blue Nun Gold Edition» 0.75լ",
    )
    repo = unit_of_work.discounted_product_read_model_repo
    discounted_product_read_models = [
        make_discounted_product_read_model(
            created_at=created_at,
            discounted_product_uuid=str(uuid.uuid4()),
        )
        for _ in range(15)
    ]
    discounted_product_read_models.append(discounted_product_read_model_)
    await repo.add_many(discounted_product_read_models)
    await refresh_opensearch_index(index_or_alias_name=discounted_product_read_model.ALIAS_NAME)

    # when
    found_products, scroll_id = await repo.get_by_name_page(name=query, size=1)

    # then
    # first_page
    assert scroll_id is not None
    assert len(found_products) == 1
    found_product = found_products[0]
    assert found_product["discounted_product_uuid"] == discounted_product_read_model_["discounted_product_uuid"]
    assert found_product["name"] == discounted_product_read_model_["name"]

    # second page
    found_products, scroll_id = await repo.get_by_name_page(name=query, size=1, scroll_id=scroll_id)
    assert scroll_id is None
    assert len(found_products) == 0
