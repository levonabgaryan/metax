import datetime as dt
import uuid

import pytest

from metax.core.application.cud_services.retailer import (
    DeleteRetailerService,
)
from metax.core.application.cud_services.retailer.dtos import DeleteRetailerRequestDTO, DeleteRetailerResponseDTO
from metax.core.application.ports.ddd_patterns.repository.errors import EntityIsNotFoundError
from metax_lifespan import MetaxAppLifespanManager
from tests.utils import make_discounted_product_entity, make_retailer_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_delete_retailer_service_deletes_retailer(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    metax_container = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work_provider = metax_container.get_unit_of_work_provider()
    event_bus = await metax_container.get_event_bus()
    unit_of_work = metax_container.get_unit_of_work()

    retailer = make_retailer_entity()
    async with unit_of_work as uow:
        await uow.retailer_repo.add(retailer)
        await uow.commit()

    request_dto = DeleteRetailerRequestDTO(retailer_uuid=retailer.get_uuid())
    service = DeleteRetailerService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
    response_dto = await service.execute(request_dto)

    assert isinstance(response_dto, DeleteRetailerResponseDTO)
    assert response_dto.retailer_uuid == retailer.get_uuid()

    uow = await unit_of_work_provider.provide()
    async with uow:
        with pytest.raises(EntityIsNotFoundError):
            await uow.retailer_repo.get_by_uuid(retailer.get_uuid())


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_delete_retailer_service_deletes_discounted_products_first(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    metax_container = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work_provider = metax_container.get_unit_of_work_provider()
    event_bus = await metax_container.get_event_bus()
    unit_of_work = metax_container.get_unit_of_work()

    retailer = make_retailer_entity()
    product = make_discounted_product_entity(
        retailer_uuid=retailer.get_uuid(),
        created_at=dt.datetime.now(tz=dt.UTC),
    )
    async with unit_of_work as uow:
        await uow.retailer_repo.add(retailer)
        await uow.discounted_product_repo.add_many([product])
        await uow.commit()

    request_dto = DeleteRetailerRequestDTO(retailer_uuid=retailer.get_uuid())
    service = DeleteRetailerService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
    await service.execute(request_dto)

    uow = await unit_of_work_provider.provide()
    async with uow:
        with pytest.raises(EntityIsNotFoundError):
            await uow.retailer_repo.get_by_uuid(retailer.get_uuid())
        with pytest.raises(EntityIsNotFoundError):
            await uow.discounted_product_repo.get_by_uuid(product.get_uuid())


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_delete_retailer_service_raises_when_retailer_missing(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    metax_container = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work_provider = metax_container.get_unit_of_work_provider()
    event_bus = await metax_container.get_event_bus()

    missing_uuid = uuid.uuid4()
    request_dto = DeleteRetailerRequestDTO(retailer_uuid=missing_uuid)
    service = DeleteRetailerService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)

    with pytest.raises(EntityIsNotFoundError):
        await service.execute(request_dto)
