from datetime import UTC, datetime

import pytest

from metax.core.application.event_handlers.category.events import CategoryUpdated
from metax.core.application.read_models.discounted_product import DiscountedProductReadModel
from metax.frameworks_and_drivers.opensearch.indices import discounted_product_read_model
from metax_lifespan import MetaxAppLifespanManager
from tests.integration.conftest import refresh_opensearch_index
from tests.utils import (
    make_category_entity,
    make_discounted_product_entity,
    make_retailer_entity,
)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_event_handler_shall_update_category_in_read_model(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_integration_tests.get_di_container()
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()
    repos = metax_container_for_integration_tests.repositories_container.container
    discounted_product_read_model_repository = await repos.discounted_product_read_model_repository.async_()
    event_bus = await metax_container_for_integration_tests.resources_container.container.event_bus.async_()
    creation_date = datetime.now(tz=UTC)
    category = make_category_entity(name="test_name")
    retailer = make_retailer_entity()
    discounted_product = make_discounted_product_entity(
        retailer_uuid=retailer.get_uuid(), category_uuid=category.get_uuid(), created_at=creation_date
    )

    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.retailer_repo.add(retailer)
        await uow.discounted_product_repo.add_many(discounted_products=[discounted_product])
        await uow.commit()

    created_iso = discounted_product.get_created_at().isoformat()
    updated_iso = discounted_product.get_updated_at().isoformat()
    discounted_product_read_model_ = DiscountedProductReadModel(
        uuid_=str(discounted_product.get_uuid()),
        name=discounted_product.get_name(),
        real_price=float(discounted_product.get_real_price()),
        discounted_price=float(discounted_product.get_discounted_price()),
        created_at=created_iso,
        updated_at=updated_iso,
        url=discounted_product.get_url(),
        retailer={
            "uuid_": str(retailer.get_uuid()),
            "created_at": retailer.get_created_at().isoformat(),
            "updated_at": retailer.get_updated_at().isoformat(),
            "name": retailer.get_name(),
            "home_page_url": retailer.get_home_page_url(),
            "phone_number": retailer.get_phone_number(),
        },
        category={
            "uuid_": str(category.get_uuid()),
            "created_at": category.get_created_at().isoformat(),
            "updated_at": category.get_updated_at().isoformat(),
            "name": category.get_name(),
        },
    )
    await discounted_product_read_model_repository.add_many([discounted_product_read_model_])
    await refresh_opensearch_index(
        metax_lifespan_manager_for_integration_tests, discounted_product_read_model.ALIAS_NAME
    )
    async with unit_of_work as uow:
        found_category = await uow.category_repo.get_by_uuid(category.get_uuid())
        found_category.set_name("test_new_name")
        await uow.category_repo.update(found_category)
        await uow.commit()

    event = CategoryUpdated(
        category_uuid=found_category.get_uuid(),
    )
    # when
    await event_bus.emit_and_wait(event)

    # then
    await refresh_opensearch_index(
        metax_lifespan_manager_for_integration_tests, discounted_product_read_model.ALIAS_NAME
    )
    updated_category_in_read_model = await discounted_product_read_model_repository.get_by_uuid(
        uuid_=str(discounted_product.get_uuid())
    )

    assert updated_category_in_read_model["category"]["name"] == "test_new_name"
