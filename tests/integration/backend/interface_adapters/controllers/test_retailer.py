import pytest

from backend.core.application.ports.patterns.unit_of_work import UnitOfWork
from backend.interface_adapters.controllers.retailer import RetailerController
from tests.integration.conftest import make_retailer_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_retailer_controller_create(
    unit_of_work: UnitOfWork, retailer_controller: RetailerController
) -> None:
    # given
    name = "test_name"
    url = "test_url"
    phone = "test_phone"

    # when
    await retailer_controller.create(name, url, phone)

    # then
    async with unit_of_work as uow:
        retailer = await uow.repositories.retailer.get_by_name(name)
        await uow.commit()

    assert retailer.get_name() == name
    assert retailer.get_url() == url
    assert retailer.get_phone_number() == phone


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_retailer_controller_update(
    unit_of_work: UnitOfWork, retailer_controller: RetailerController
) -> None:
    # given
    retailer = make_retailer_entity()
    new_name = "new_name"
    new_url = "new_url"
    new_phone = "new_phone"

    async with unit_of_work as uow:
        await uow.repositories.retailer.add(retailer)
        await uow.commit()

    # when
    await retailer_controller.update(
        new_name=new_name,
        retailer_uuid=str(retailer.get_uuid()),
        new_url=new_url,
        new_phone_number=new_phone,
    )

    # then
    async with unit_of_work as uow:
        updated_retailer = await uow.repositories.retailer.get_by_uuid(retailer.get_uuid())

    assert updated_retailer.get_name() == new_name
    assert updated_retailer.get_url() == new_url
    assert updated_retailer.get_phone_number() == new_phone
