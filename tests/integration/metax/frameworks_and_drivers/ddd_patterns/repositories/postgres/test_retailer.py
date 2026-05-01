from uuid import uuid7

import pytest

from constants import ErrorCodes
from metax.core.application.ports.ddd_patterns.repository.errors import (
    EntityAlreadyExistsError,
    EntityIsNotFoundError,
)
from metax.core.domain.entities.retailer.value_objects import RetailersNames
from metax_lifespan import MetaxAppLifespanManager
from tests.utils import make_retailer_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_retailer_repo_add_and_get(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_integration_tests.get_di_container()
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
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_integration_tests.get_di_container()
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()

    retailer = make_retailer_entity()

    async with unit_of_work as uow:
        await uow.retailer_repo.add(retailer)
        await uow.commit()

    # when
    retailer.set_name(RetailersNames.SAS_AM.value)
    retailer.set_home_page_url("new_url")
    retailer.set_phone_number("new_phone_number")
    async with unit_of_work as uow:
        await uow.retailer_repo.update(updated_retailer=retailer)
        await uow.commit()

    # then
    retailer = await unit_of_work.retailer_repo.get_by_uuid(retailer.get_uuid())

    assert retailer.get_name() == RetailersNames.SAS_AM.value
    assert retailer.get_home_page_url() == "new_url"
    assert retailer.get_phone_number() == "new_phone_number"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_retailer_is_not_found_by_uuid(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_integration_tests.get_di_container()
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()

    random_uuid = uuid7()
    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError) as err:
            await uow.retailer_repo.get_by_uuid(random_uuid)

    # then
    assert err.value.title == "retailer not found."
    assert err.value.details == f"No retailer found by 'uuid' = '{random_uuid}'."
    assert err.value.error_code == ErrorCodes.ENTITY_IS_NOT_FOUND


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_retailer_is_not_found_by_name(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_integration_tests.get_di_container()
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()

    test_name = RetailersNames.SAS_AM.value

    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError) as err:
            await uow.retailer_repo.get_by_name(test_name)

    # then
    assert err.value.title == "retailer not found."
    assert err.value.details == f"No retailer found by 'name' = '{test_name}'."
    assert err.value.error_code == ErrorCodes.ENTITY_IS_NOT_FOUND


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_retailer_repo_get_all(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_integration_tests.get_di_container()
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()
    r_sas = make_retailer_entity(
        name=RetailersNames.SAS_AM.value,
        url="https://repo-get-all-sas.example",
        phone_number="+repo-get-all-sas",
    )
    r_yvn = make_retailer_entity(
        name=RetailersNames.YEREVAN_CITY.value,
        url="https://repo-get-all-yvn.example",
        phone_number="+repo-get-all-yvn",
    )
    async with unit_of_work as uow:
        await uow.retailer_repo.add(r_sas)
        await uow.retailer_repo.add(r_yvn)
        await uow.commit()

    # when
    async with unit_of_work as uow:
        all_retailers = [r async for r in uow.retailer_repo.all()]

    assert len(all_retailers) == 2
    assert r_sas in all_retailers
    assert r_yvn in all_retailers


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_retailer_repo_list_paginated(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_integration_tests.get_di_container()
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()
    r_sas = make_retailer_entity(
        name=RetailersNames.SAS_AM.value,
        url="https://repo-get-all-sas.example",
        phone_number="+repo-get-all-sas",
    )
    r_yvn = make_retailer_entity(
        name=RetailersNames.YEREVAN_CITY.value,
        url="https://repo-get-all-yvn.example",
        phone_number="+repo-get-all-yvn",
    )

    async with unit_of_work as uow:
        await uow.retailer_repo.add(r_sas)
        await uow.retailer_repo.add(r_yvn)
        await uow.commit()

    # when
    async with unit_of_work as uow:
        total_count_1, first_page = await uow.retailer_repo.list_paginated_and_total_count(limit=1, offset=0)
        total_count_2, second_page = await uow.retailer_repo.list_paginated_and_total_count(limit=1, offset=1)

    # then
    assert total_count_1 == total_count_2
    assert len(first_page) == 1
    assert len(second_page) == 1

    assert first_page[0].get_uuid() == r_sas.get_uuid()
    assert second_page[0].get_uuid() == r_yvn.get_uuid()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_retailer_repo_add_duplicate_name_raises_entity_already_exists(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_integration_tests.get_di_container()
    unit_of_work = metax_container.patterns_container.container.unit_of_work()
    existing = make_retailer_entity(name=RetailersNames.YEREVAN_CITY.value)
    duplicate_name = make_retailer_entity(name=RetailersNames.YEREVAN_CITY.value)

    async with unit_of_work as uow:
        await uow.retailer_repo.add(existing)
        await uow.commit()

    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityAlreadyExistsError) as err:
            await uow.retailer_repo.add(duplicate_name)

    # then
    assert err.value.error_code == ErrorCodes.ENTITY_ALREADY_EXISTS
    assert err.value.title == "retailer already exists."
    assert (
        err.value.details == f"An existing retailer was found by 'name' = '{RetailersNames.YEREVAN_CITY.value}'."
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_retailer_repo_update_duplicate_name_raises_entity_already_exists(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_integration_tests.get_di_container()
    unit_of_work = metax_container.patterns_container.container.unit_of_work()
    retailer_a = make_retailer_entity(name=RetailersNames.YEREVAN_CITY.value)
    retailer_b = make_retailer_entity(name=RetailersNames.SAS_AM.value)

    async with unit_of_work as uow:
        await uow.retailer_repo.add(retailer_a)
        await uow.retailer_repo.add(retailer_b)
        await uow.commit()

    retailer_b.set_name(retailer_a.get_name())

    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityAlreadyExistsError) as err:
            await uow.retailer_repo.update(retailer_b)

    # then
    assert err.value.error_code == ErrorCodes.ENTITY_ALREADY_EXISTS
    assert err.value.title == "retailer already exists."
    assert (
        err.value.details == f"An existing retailer was found by 'name' = '{RetailersNames.YEREVAN_CITY.value}'."
    )
