from datetime import timezone, datetime

import pytest

from backend.core.application.ports.patterns.unit_of_work import UnitOfWork
from backend.core.application.ports.repositories.retailer import RetailerFieldsToUpdate
from backend.core.domain.entities.retailer_entity.events import RetailerUpdated
from backend.core.domain.entities.retailer_entity.retailer import DataForRetailerUpdate
from backend.frameworks_and_drivers.di.event_handlers_container import RetailerEventHandlersContainer
from tests.integration.conftest import make_retailer_entity, make_discounted_product_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_event_handler_shall_update_retailer_in_read_model(
    unit_of_work: UnitOfWork, retailer_event_handlers: RetailerEventHandlersContainer
) -> None:
    # given
    retailer = make_retailer_entity(name="test_retailer")
    discounted_product = make_discounted_product_entity(retailer_uuid=retailer.get_uuid())
    creation_date = datetime.now(tz=timezone.utc)

    async with unit_of_work as uow:
        await uow.repositories.retailer.add(retailer)
        await uow.repositories.discounted_product.add_many_by_date(
            discounted_products=[discounted_product], started_time=creation_date
        )
        await uow.commit()

    async with unit_of_work as uow:
        found_retailer = await uow.repositories.retailer.get_by_uuid(retailer_uuid=retailer.get_uuid())
        new_data = DataForRetailerUpdate(new_name="test_retailer_new_name")
        found_retailer.update(new_data)
        fields_to_update = RetailerFieldsToUpdate(name=True)
        await uow.repositories.retailer.update(updated_retailer=found_retailer, fields_to_update=fields_to_update)
        await uow.commit()

    event = RetailerUpdated(found_retailer.get_uuid())

    event_handler = retailer_event_handlers.update_discounted_product_read_model()

    # when
    await event_handler.handle(event)

    # then
    async with unit_of_work as uow:
        updated_retailer = await uow.repositories.retailer.get_by_uuid(retailer_uuid=retailer.get_uuid())
        await uow.commit()

    assert updated_retailer.get_name() == "test_retailer_new_name"
