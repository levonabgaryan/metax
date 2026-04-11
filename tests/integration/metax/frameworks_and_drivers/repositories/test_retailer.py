from uuid import uuid7

import pytest

from metax.core.application.ports.ddd_patterns.repository.errors.errors import EntityIsNotFoundError
from metax.core.domain.entities.retailer.entity import DataForRetailerUpdate
from metax.core.domain.entities.retailer.value_objects import RetailersNames
from metax.frameworks_and_drivers.di.metax_container import MetaxContainer
from tests.utils import make_retailer_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_retailer_repo_add_and_get(metax_container_for_integration_tests: MetaxContainer) -> None:
    # given
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()

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
async def test_retailer_repo_update(
    metax_container_for_integration_tests: MetaxContainer,
) -> None:
    # given
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()

    retailer = make_retailer_entity()

    async with unit_of_work as uow:
        await uow.retailer_repo.add(retailer)
        await uow.commit()

    new_data = DataForRetailerUpdate(
        new_name=RetailersNames.SAS_AM.value,
        new_url="new_url",
        new_phone_number="new_phone_number",
    )
    # when
    retailer.update(new_data=new_data)
    async with unit_of_work as uow:
        await uow.retailer_repo.update(updated_retailer=retailer)
        await uow.commit()

    # then
    retailer = await unit_of_work.retailer_repo.get_by_uuid(retailer.get_uuid())

    assert retailer.get_name() == RetailersNames.SAS_AM
    assert retailer.get_home_page_url() == "new_url"
    assert retailer.get_phone_number() == "new_phone_number"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_retailer_is_not_found_by_uuid(metax_container_for_integration_tests: MetaxContainer) -> None:
    # given
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()

    random_uuid = uuid7()
    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError) as err:
            await uow.retailer_repo.get_by_uuid(random_uuid)

    # then
    assert err.value.title == f"There is no retailer entity found by field 'uuid' with value '{random_uuid}'."
    assert err.value.error_code == "RETAILER_IS_NOT_FOUND"
    assert err.value.details == {"searched_field_name": "uuid", "searched_field_value": f"{random_uuid}"}


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_retailer_is_not_found_by_name(metax_container_for_integration_tests: MetaxContainer) -> None:
    # given
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()

    test_name = RetailersNames.SAS_AM

    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError) as err:
            await uow.retailer_repo.get_by_name(test_name)

    # then
    assert err.value.title == f"There is no retailer entity found by field 'name' with value '{test_name}'."
    assert err.value.error_code == "RETAILER_IS_NOT_FOUND"
    assert err.value.details == {"searched_field_name": "name", "searched_field_value": f"{test_name}"}
