from datetime import timezone, datetime

import pytest


from metax.core.application.ports.repositories.entites_repositories.retailer import (
    RetailerFieldsToUpdate,
)
from metax.core.application.read_models.discounted_product import DiscountedProductReadModel
from metax.core.application.event_handlers.retailer.events import RetailerUpdated
from metax.core.domain.entities.retailer.entity import DataForRetailerUpdate
from metax.core.domain.entities.retailer.value_objects import RetailersNames
from metax.frameworks_and_drivers.di.bootstrap import ServiceContainer
from metax.frameworks_and_drivers.opensearch.indices import discounted_product_read_model
from tests.utils import (
    make_retailer_entity,
    make_discounted_product_entity,
)
from tests.integration.conftest import refresh_opensearch_index


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_event_handler_shall_update_retailer_in_read_model(
    service_container_for_integration_tests: ServiceContainer,
) -> None:
    # given
    unit_of_work = await service_container_for_integration_tests.patterns_container.container.unit_of_work.async_()
    event_bus = await service_container_for_integration_tests.patterns_container.container.event_bus.async_()
    retailer = make_retailer_entity()
    discounted_product = make_discounted_product_entity(
        retailer_uuid=retailer.get_uuid(), created_at=datetime.now(tz=timezone.utc)
    )

    async with unit_of_work as uow:
        await uow.retailer_repo.add(retailer)
        await uow.discounted_product_repo.add_many(discounted_products=[discounted_product])
        await uow.commit()

    discounted_product_read_model_ = DiscountedProductReadModel(
        discounted_product_uuid=str(discounted_product.get_uuid()),
        name=discounted_product.get_name(),
        real_price=float(discounted_product.get_real_price()),
        discounted_price=float(discounted_product.get_discounted_price()),
        retailer_uuid=str(discounted_product.get_retailer_uuid()),
        retailer_name=retailer.get_name().value,
        created_at=discounted_product.get_created_at().isoformat(),
    )
    await unit_of_work.discounted_product_read_model_repo.add_many([discounted_product_read_model_])
    await refresh_opensearch_index(index_or_alias_name=discounted_product_read_model.ALIAS_NAME)

    async with unit_of_work as uow:
        found_retailer = await uow.retailer_repo.get_by_uuid(retailer_uuid=retailer.get_uuid())
        new_data = DataForRetailerUpdate(new_name=RetailersNames.SAS_AM.value)
        found_retailer.update(new_data)
        fields_to_update = RetailerFieldsToUpdate(name=True)
        await uow.retailer_repo.update(updated_retailer=found_retailer, fields_to_update=fields_to_update)
        await uow.commit()

    event = RetailerUpdated(found_retailer.get_uuid())

    # when
    await event_bus.handle(event)
    await refresh_opensearch_index(index_or_alias_name=discounted_product_read_model.ALIAS_NAME)

    # then
    async with unit_of_work as uow:
        updated_retailer = await unit_of_work.discounted_product_read_model_repo.get_by_uuid(
            str(discounted_product.get_uuid())
        )
        await uow.commit()

    assert updated_retailer["retailer_name"] == RetailersNames.SAS_AM.value
