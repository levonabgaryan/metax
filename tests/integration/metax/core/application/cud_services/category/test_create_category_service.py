import pytest

from metax.core.application.cud_services.category import (
    CreateCategoryRequestDTO,
    CreateCategoryResponseDTO,
    CreateCategoryService,
)
from metax_lifespan import MetaxAppLifespanManager


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_create_category_service(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work_provider = metax_container.get_unit_of_work_provider()
    event_bus = await metax_container.get_event_bus()
    request_dto = CreateCategoryRequestDTO(
        name="Test Category",
        name_hy="Թեստ",
        name_ru="Тест",
    )

    # when
    service = CreateCategoryService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
    response_dto = await service.execute(request_dto)

    # then
    assert isinstance(response_dto, CreateCategoryResponseDTO)
    assert response_dto.name == request_dto.name
    assert response_dto.name_hy == request_dto.name_hy
    assert response_dto.name_ru == request_dto.name_ru

    uow = await unit_of_work_provider.provide()
    async with uow:
        category = await uow.category_repo.get_by_uuid(response_dto.category_uuid)
    assert category.get_uuid() == response_dto.category_uuid
    assert category.get_name() == request_dto.name
    assert category.get_name_hy() == request_dto.name_hy
    assert category.get_name_ru() == request_dto.name_ru


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_create_category_service_with_defaults(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work_provider = metax_container.get_unit_of_work_provider()
    event_bus = await metax_container.get_event_bus()
    request_dto = CreateCategoryRequestDTO(name="Category Without Translations")

    # when
    service = CreateCategoryService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
    response_dto = await service.execute(request_dto)

    # then
    assert isinstance(response_dto, CreateCategoryResponseDTO)
    assert response_dto.name == request_dto.name
    assert response_dto.name_hy == ""
    assert response_dto.name_ru == ""

    uow = await unit_of_work_provider.provide()
    async with uow:
        category = await uow.category_repo.get_by_uuid(response_dto.category_uuid)
    assert category.get_uuid() == response_dto.category_uuid
    assert category.get_name() == request_dto.name
