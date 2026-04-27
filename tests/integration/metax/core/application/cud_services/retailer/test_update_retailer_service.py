import pytest

from metax.core.application.cud_services.retailer import (
    UpdateRetailerRequestDTO,
    UpdateRetailerService,
)
from metax.core.application.cud_services.retailer.dtos import UpdateRetailerResponseDTO
from metax.core.domain.entities.retailer.value_objects import RetailersNames
from metax_lifespan import MetaxAppLifespanManager
from tests.utils import make_retailer_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_retailer_service(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_integration_tests.get_di_container()
    unit_of_work_provider = (
        metax_container_for_integration_tests.patterns_container.container.unit_of_work_provider()
    )
    event_bus = await metax_container_for_integration_tests.resources_container.container.event_bus.async_()
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()

    retailer = make_retailer_entity()
    request_dto = UpdateRetailerRequestDTO(
        retailer_uuid=retailer.get_uuid(),
        new_name=RetailersNames.SAS_AM.value,
        new_url="test_new_url",
        new_phone_number="test_new_phone_number",
    )

    async with unit_of_work as uow:
        await uow.retailer_repo.add(retailer)
        await uow.commit()

    # when
    service = UpdateRetailerService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
    response_dto = await service.execute(request_dto)

    # then
    assert isinstance(response_dto, UpdateRetailerResponseDTO)
    assert response_dto.retailer_uuid == retailer.get_uuid()
    assert response_dto.new_name == RetailersNames.SAS_AM.value
    assert response_dto.new_url == "test_new_url"
    assert response_dto.new_phone_number == "test_new_phone_number"

    uow = await unit_of_work_provider.provide()
    async with uow:
        updated_retailer = await uow.retailer_repo.get_by_uuid(retailer.get_uuid())
        await uow.commit()

    assert updated_retailer.get_name() == RetailersNames.SAS_AM.value
    assert updated_retailer.get_home_page_url() == "test_new_url"
    assert updated_retailer.get_phone_number() == "test_new_phone_number"
