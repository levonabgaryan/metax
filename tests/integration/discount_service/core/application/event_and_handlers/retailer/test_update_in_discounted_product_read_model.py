from datetime import timezone, datetime

import pytest
from dependency_injector.wiring import Provide, inject

from discount_service.core.application.event_and_handlers.retailer.update_in_discounted_product_read_model import (
    UpdateRetailerInDiscountedProductReadModel,
)
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.core.application.ports.repositories.entites_repositories.retailer import (
    RetailerFieldsToUpdate,
)
from discount_service.core.application.read_models.discounted_product import DiscountedProductReadModel
from discount_service.core.domain.entities.retailer_entity.events import RetailerUpdated
from discount_service.core.domain.entities.retailer_entity.retailer import DataForRetailerUpdate
from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer
from discount_service.frameworks_and_drivers.opensearch.indices import discounted_product_read_model
from tests.utils import (
    make_retailer_entity,
    make_discounted_product_entity,
    clear_opensearch_db,
    refresh_opensearch_index,
)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@clear_opensearch_db
@inject
async def test_event_handler_shall_update_retailer_in_read_model(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
    event_handler: UpdateRetailerInDiscountedProductReadModel = Provide[
        ServiceContainer.event_handlers_container.container.retailer.container.update_discounted_product_read_model
    ],
) -> None:
    # given
    retailer = make_retailer_entity(name="test_retailer")
    discounted_product = make_discounted_product_entity(
        retailer_uuid=retailer.get_uuid(), created_at=datetime.now(tz=timezone.utc)
    )

    async with unit_of_work as uow:
        await uow.retailer_repo.add(retailer)
        await uow.discounted_product_repo.add_many(discounted_products=[discounted_product])
        await uow.commit()

    async with unit_of_work as uow:
        found_retailer = await uow.retailer_repo.get_by_uuid(retailer_uuid=retailer.get_uuid())
        new_data = DataForRetailerUpdate(new_name="test_retailer_new_name")
        found_retailer.update(new_data)
        fields_to_update = RetailerFieldsToUpdate(name=True)
        await uow.retailer_repo.update(updated_retailer=found_retailer, fields_to_update=fields_to_update)
        await uow.commit()

    discounted_product_read_model_ = DiscountedProductReadModel(
        discounted_product_uuid=str(discounted_product.get_uuid()),
        name=discounted_product.get_name(),
        real_price=float(discounted_product.get_real_price()),
        discounted_price=float(discounted_product.get_discounted_price()),
        retailer_uuid=str(discounted_product.get_retailer_uuid()),
        retailer_name=retailer.get_name(),
        created_at=discounted_product.get_created_at().isoformat(),
    )
    await unit_of_work.discounted_product_read_model_repo.add_many([discounted_product_read_model_])
    await refresh_opensearch_index(index_or_alias_name=discounted_product_read_model.ALIAS_NAME)
    event = RetailerUpdated(found_retailer.get_uuid())

    event_handler_ = event_handler

    # when
    await event_handler_.handle(event)
    await refresh_opensearch_index(index_or_alias_name=discounted_product_read_model.ALIAS_NAME)

    # then
    updated_retailer = await unit_of_work.discounted_product_read_model_repo.get_by_uuid(
        str(discounted_product.get_uuid())
    )

    assert updated_retailer["retailer_name"] == "test_retailer_new_name"
