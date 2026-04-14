from uuid import uuid7

import pytest

from metax.core.application.ports.ddd_patterns.repository.errors import EntityIsNotFoundError
from metax.core.domain.entities.retailer.value_objects import RetailersNames
from metax_application import MetaxApplication
from tests.utils import make_retailer_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_retailer_repo_add_and_get(metax_app_for_integration_tests: MetaxApplication) -> None:
    # given
    metax_container_for_integration_tests = metax_app_for_integration_tests.get_di_container()
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
    metax_app_for_integration_tests: MetaxApplication,
) -> None:
    # given
    metax_container_for_integration_tests = metax_app_for_integration_tests.get_di_container()
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()

    retailer = make_retailer_entity()

    async with unit_of_work as uow:
        await uow.retailer_repo.add(retailer)
        await uow.commit()

    # when
    retailer.set_name(RetailersNames.SAS_AM)
    retailer.set_home_page_url("new_url")
    retailer.set_phone_number("new_phone_number")
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
async def test_retailer_is_not_found_by_uuid(metax_app_for_integration_tests: MetaxApplication) -> None:
    # given
    metax_container_for_integration_tests = metax_app_for_integration_tests.get_di_container()
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()

    random_uuid = uuid7()
    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError) as err:
            await uow.retailer_repo.get_by_uuid(random_uuid)

    # then
    assert err.value.title == f"There is no retailer entity found by field 'uuid' with value '{random_uuid}'."
    assert err.value.error_code == "ENTITY_IS_NOT_FOUND"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_retailer_is_not_found_by_name(metax_app_for_integration_tests: MetaxApplication) -> None:
    # given
    metax_container_for_integration_tests = metax_app_for_integration_tests.get_di_container()
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()

    test_name = RetailersNames.SAS_AM

    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError) as err:
            await uow.retailer_repo.get_by_name(test_name)

    # then
    assert err.value.title == f"There is no retailer entity found by field 'name' with value '{test_name}'."
    assert err.value.error_code == "ENTITY_IS_NOT_FOUND"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_retailer_repo_get_all(metax_app_for_integration_tests: MetaxApplication) -> None:
    # given
    metax_container_for_integration_tests = metax_app_for_integration_tests.get_di_container()
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()
    r_sas = make_retailer_entity(
        name=RetailersNames.SAS_AM,
        url="https://repo-get-all-sas.example",
        phone_number="+repo-get-all-sas",
    )
    r_yvn = make_retailer_entity(
        name=RetailersNames.YEREVAN_CITY,
        url="https://repo-get-all-yvn.example",
        phone_number="+repo-get-all-yvn",
    )
    async with unit_of_work as uow:
        await uow.retailer_repo.add(r_sas)
        await uow.retailer_repo.add(r_yvn)
        await uow.commit()

    # when
    async with unit_of_work as uow:
        all_retailers = [r async for r in uow.retailer_repo.get_all()]

    assert len(all_retailers) == 2
    assert r_sas in all_retailers
    assert r_yvn in all_retailers
