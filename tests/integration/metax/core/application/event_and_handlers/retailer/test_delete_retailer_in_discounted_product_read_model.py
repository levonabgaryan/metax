import datetime as dt

import pytest
from opensearchpy.exceptions import NotFoundError

from metax.core.application.event_handlers.retailer.events import RetailerDeleted
from metax.core.application.read_models.discounted_product import DiscountedProductReadModel
from metax.frameworks_and_drivers.opensearch.indices import discounted_product_read_model
from metax_lifespan import MetaxAppLifespanManager
from tests.conftest import refresh_opensearch_index
from tests.utils import make_discounted_product_entity, make_retailer_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_event_handler_shall_delete_discounted_products_by_retailer_from_read_model(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    metax_container = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work = metax_container.get_unit_of_work()
    discounted_product_read_model_repository = await metax_container.get_discounted_product_read_model_repository()
    event_bus = await metax_container.get_event_bus()
    retailer = make_retailer_entity()
    discounted_product = make_discounted_product_entity(
        retailer_uuid=retailer.get_uuid(), created_at=dt.datetime.now(tz=dt.UTC)
    )

    async with unit_of_work as uow:
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
    )
    await discounted_product_read_model_repository.add_many([discounted_product_read_model_])
    await refresh_opensearch_index(metax_lifespan_manager_for_tests, discounted_product_read_model.ALIAS_NAME)

    product_uuid = str(discounted_product.get_uuid())
    await discounted_product_read_model_repository.get_by_uuid(product_uuid)

    event = RetailerDeleted(retailer_uuid=retailer.get_uuid())

    await event_bus.emit_and_wait(event)
    await refresh_opensearch_index(metax_lifespan_manager_for_tests, discounted_product_read_model.ALIAS_NAME)

    with pytest.raises(NotFoundError):
        await discounted_product_read_model_repository.get_by_uuid(product_uuid)
