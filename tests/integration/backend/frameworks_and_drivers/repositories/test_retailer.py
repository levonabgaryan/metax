from uuid import uuid4

import pytest

from backend.core.application.ports.patterns.unit_of_work import UnitOfWork
from backend.core.application.ports.repositories.errors.errors import EntityIsNotFoundError
from backend.core.application.ports.repositories.retailer import RetailerFieldsToUpdate
from backend.core.domain.entities.retailer_entity.retailer import Retailer, DataForRetailerUpdate


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_retailer_repo_add_and_get(unit_of_work: UnitOfWork) -> None:
    # given
    retailer_uuid = uuid4()
    name = "test_name"
    retailer = Retailer(retailer_uuid=retailer_uuid, name=name, url="test_url", phone_number="test_number")

    # when
    async with unit_of_work as uow:
        await uow.repositories.retailer.add(retailer)
        await uow.commit()

    # then
    async with unit_of_work as uow:
        got_retailer_by_uuid = await uow.repositories.retailer.get_by_uuid(retailer_uuid)
        got_retailer_by_name = await uow.repositories.retailer.get_by_name(name)

        assert got_retailer_by_uuid.get_uuid() == retailer_uuid
        assert got_retailer_by_uuid.get_name() == name

        assert got_retailer_by_name.get_uuid() == retailer_uuid
        assert got_retailer_by_name.get_name() == name


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_retailer_repo_update(unit_of_work: UnitOfWork) -> None:
    # given
    retailer_uuid = uuid4()
    name = "test_name"
    retailer = Retailer(retailer_uuid=retailer_uuid, name=name, url="test_url", phone_number="test_number")

    async with unit_of_work as uow:
        await uow.repositories.retailer.add(retailer)
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
        await uow.repositories.retailer.update(updated_retailer=retailer, fields_to_update=fields_to_update)
        await uow.commit()

    # then
    async with unit_of_work as uow:
        retailer = await uow.repositories.retailer.get_by_uuid(retailer_uuid)
        await uow.commit()

    assert retailer.get_name() == "new_test_name"
    assert retailer.get_url() == "new_test_url"
    assert retailer.get_phone_number() == "new_test_phone_number"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_retailer_is_not_found_by_uuid(unit_of_work: UnitOfWork) -> None:
    # given
    random_uuid = uuid4()
    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError) as err:
            await uow.repositories.retailer.get_by_uuid(random_uuid)

    # then
    assert err.value.message == f"There is no retailer entity found by field 'uuid' with value '{random_uuid}'."
    assert err.value.error_code == "RETAILER_IS_NOT_FOUND"
    assert err.value.details == {"searched_field_name": "uuid", "searched_field_value": f"{random_uuid}"}


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_retailer_is_not_found_by_name(unit_of_work: UnitOfWork) -> None:
    # given
    test_name = "test_name"

    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError) as err:
            await uow.repositories.retailer.get_by_name(test_name)

    # then
    assert err.value.message == f"There is no retailer entity found by field 'name' with value '{test_name}'."
    assert err.value.error_code == "RETAILER_IS_NOT_FOUND"
    assert err.value.details == {"searched_field_name": "name", "searched_field_value": f"{test_name}"}
