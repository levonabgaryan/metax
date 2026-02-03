from uuid import uuid4

import pytest
from dependency_injector.wiring import inject, Provide

from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.core.application.ports.repositories.errors.errors import EntityIsNotFoundError
from discount_service.core.application.ports.repositories.entites_repositories.retailer import (
    RetailerFieldsToUpdate,
)
from discount_service.core.domain.entities.retailer_entity.retailer import DataForRetailerUpdate
from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer
from tests.utils import make_retailer_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@inject
async def test_retailer_repo_add_and_get(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
) -> None:
    # given
    retailer = make_retailer_entity()

    # when
    async with unit_of_work as uow:
        await uow.retailer_repo.add(retailer)
        await uow.commit()

    # then
    got_retailer_by_uuid = await unit_of_work.retailer_repo.get_by_uuid(retailer.get_uuid())
    got_retailer_by_name = await unit_of_work.retailer_repo.get_by_name(retailer.get_name())

    assert got_retailer_by_uuid.get_uuid() == retailer.get_uuid()
    assert got_retailer_by_uuid.get_name() == retailer.get_name()

    assert got_retailer_by_name.get_uuid() == retailer.get_uuid()
    assert got_retailer_by_name.get_name() == retailer.get_name()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@inject
async def test_retailer_repo_update(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
) -> None:
    # given
    retailer = make_retailer_entity()

    async with unit_of_work as uow:
        await uow.retailer_repo.add(retailer)
        await uow.commit()

    new_data = DataForRetailerUpdate(
        new_name="new_name",
        new_url="new_url",
        new_phone_number="new_phone_number",
    )
    fields_to_update = RetailerFieldsToUpdate(
        name=True,
        url=True,
        phone_number=True,
    )

    # when
    retailer.update(new_data=new_data)
    async with unit_of_work as uow:
        await uow.retailer_repo.update(updated_retailer=retailer, fields_to_update=fields_to_update)
        await uow.commit()

    # then
    retailer = await unit_of_work.retailer_repo.get_by_uuid(retailer.get_uuid())
    await uow.commit()

    assert retailer.get_name() == "new_name"
    assert retailer.get_url() == "new_url"
    assert retailer.get_phone_number() == "new_phone_number"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@inject
async def test_retailer_is_not_found_by_uuid(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
) -> None:
    # given
    random_uuid = uuid4()
    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError) as err:
            await uow.retailer_repo.get_by_uuid(random_uuid)

    # then
    assert err.value.message == f"There is no retailer entity found by field 'uuid' with value '{random_uuid}'."
    assert err.value.error_code == "RETAILER_IS_NOT_FOUND"
    assert err.value.details == {"searched_field_name": "uuid", "searched_field_value": f"{random_uuid}"}


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@inject
async def test_retailer_is_not_found_by_name(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
) -> None:
    # given
    test_name = "test_name"

    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError) as err:
            await uow.retailer_repo.get_by_name(test_name)

    # then
    assert err.value.message == f"There is no retailer entity found by field 'name' with value '{test_name}'."
    assert err.value.error_code == "RETAILER_IS_NOT_FOUND"
    assert err.value.details == {"searched_field_name": "name", "searched_field_value": f"{test_name}"}
