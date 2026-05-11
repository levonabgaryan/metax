import uuid

import pytest

from metax.core.application.cud_services.category import DeleteCategoryRequestDTO, DeleteCategoryService
from metax.core.application.cud_services.category.dtos import DeleteCategoryResponseDTO
from metax.core.application.ports.ddd_patterns.repository.errors import EntityIsNotFoundError
from metax_lifespan import MetaxAppLifespanManager
from tests.utils import make_category_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_delete_category_service_deletes_category(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work_provider = metax_container.get_unit_of_work_provider()
    event_bus = await metax_container.get_event_bus()
    unit_of_work = metax_container.get_unit_of_work()

    category = make_category_entity()
    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    request_dto = DeleteCategoryRequestDTO(category_uuid=category.get_uuid())
    service = DeleteCategoryService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
    # when
    response_dto = await service.execute(request_dto)

    # then
    assert isinstance(response_dto, DeleteCategoryResponseDTO)
    assert response_dto.category_uuid == category.get_uuid()

    uow = await unit_of_work_provider.provide()
    async with uow:
        with pytest.raises(EntityIsNotFoundError):
            await uow.category_repo.get_by_uuid(category.get_uuid())


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_delete_category_service_raises_when_category_missing(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work_provider = metax_container.get_unit_of_work_provider()
    event_bus = await metax_container.get_event_bus()

    missing_uuid = uuid.uuid4()
    request_dto = DeleteCategoryRequestDTO(category_uuid=missing_uuid)
    service = DeleteCategoryService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)

    # expect
    with pytest.raises(EntityIsNotFoundError):
        await service.execute(request_dto)
