import pytest

from metax.core.application.cud_services.retailer import (
    CreateRetailerRequestDTO,
    CreateRetailerService,
)
from metax.core.application.cud_services.retailer.dtos import CreateRetailerResponseDTO
from metax.core.domain.entities.retailer.value_objects import RetailersNames
from metax_lifespan import MetaxAppLifespanManager


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_create_retailer_service(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_integration_tests.get_metax_container()
    unit_of_work_provider = metax_container.get_unit_of_work_provider()
    event_bus = await metax_container.get_event_bus()
    request_dto = CreateRetailerRequestDTO(
        name=RetailersNames.YEREVAN_CITY,
        url="https://example.com",
        phone_number="test_phone_number",
    )

    # when
    service = CreateRetailerService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
    response_dto = await service.execute(request_dto)

    # then
    assert isinstance(response_dto, CreateRetailerResponseDTO)
    assert response_dto.retailer_uuid
    assert response_dto.name == RetailersNames.YEREVAN_CITY.value
    assert response_dto.home_page_url == "https://example.com"
    assert response_dto.phone_number == "test_phone_number"

    uow = await unit_of_work_provider.provide()
    async with uow:
        retailer = await uow.retailer_repo.get_by_uuid(response_dto.retailer_uuid)

    assert retailer.get_name() == RetailersNames.YEREVAN_CITY.value
    assert retailer.get_home_page_url() == "https://example.com"
    assert retailer.get_phone_number() == "test_phone_number"
