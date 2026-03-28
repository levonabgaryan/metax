from datetime import datetime, timezone

import pytest

from metax.core.application.event_handlers.discounted_product.events import (
    OldDiscountedProductsDeleted,
)

from metax.core.application.read_models.discounted_product import DiscountedProductReadModel
from metax.frameworks_and_drivers.di.metax_container import MetaxContainer
from metax.frameworks_and_drivers.opensearch.indices import discounted_product_read_model
from tests.utils import (
    make_retailer_entity,
    make_discounted_product_entity,
)
from tests.integration.conftest import refresh_opensearch_index


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_event_handler_shall_save_in_empty_read_model(
    metax_container_for_integration_tests: MetaxContainer,
) -> None:
    # given
    unit_of_work = await metax_container_for_integration_tests.patterns_container.container.unit_of_work.async_()
    event_bus = metax_container_for_integration_tests.patterns_container.container.event_bus()
    creation_data = datetime.now(tz=timezone.utc)
    retailer = make_retailer_entity()
    discounted_products = [
        make_discounted_product_entity(retailer_uuid=retailer.get_uuid(), created_at=creation_data),
        make_discounted_product_entity(retailer_uuid=retailer.get_uuid(), created_at=creation_data),
    ]
    async with unit_of_work as uow:
        await uow.retailer_repo.add(retailer)
        await uow.discounted_product_repo.add_many(discounted_products)
        await uow.commit()

    discounted_product_read_models_: list[DiscountedProductReadModel] = []
    for product in discounted_products:
        discounted_product_read_models_.append(
            DiscountedProductReadModel(
                discounted_product_uuid=str(product.get_uuid()),
                name=product.get_name(),
                real_price=float(product.get_real_price()),
                discounted_price=float(product.get_discounted_price()),
                retailer_uuid=str(product.get_retailer_uuid()),
                retailer_name=retailer.get_name().value,
                created_at=product.get_created_at().isoformat(),
            )
        )

    await unit_of_work.discounted_product_read_model_repo.add_many(discounted_product_read_models_)

    await refresh_opensearch_index(metax_container_for_integration_tests, discounted_product_read_model.ALIAS_NAME)
    event = OldDiscountedProductsDeleted(
        new_discounted_products_creation_date=creation_data,
    )

    # when
    await event_bus.handle(event)

    # then
    await refresh_opensearch_index(metax_container_for_integration_tests, discounted_product_read_model.ALIAS_NAME)
    assert await uow.discounted_product_read_model_repo.get_all_count() == 2
    read_model: DiscountedProductReadModel
    async for read_model in uow.discounted_product_read_model_repo.get_all():
        assert read_model["discounted_product_uuid"] in {
            str(product.get_uuid()) for product in discounted_products
        }
        assert read_model["created_at"] == creation_data.isoformat()
