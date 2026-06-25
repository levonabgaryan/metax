import pytest

from metax.core.application.cud_services.category import (
    UpdateCategoryRequestDTO,
    UpdateCategoryResponseDTO,
    UpdateCategoryService,
)
from metax_lifespan import MetaxAppLifespanManager
from tests.utils import make_category_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_category_service(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work_provider = metax_container.get_unit_of_work_provider()
    event_bus = await metax_container.get_event_bus()
    unit_of_work = metax_container.get_unit_of_work()
    category = make_category_entity(name_hy="հին", name_ru="старый")

    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    # when
    request_dto = UpdateCategoryRequestDTO(
        category_uuid=category.get_uuid(),
        new_name="new_test_name",
        new_name_hy="նոր",
    )
    service = UpdateCategoryService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
    response_dto = await service.execute(request_dto)

    # then
    assert isinstance(response_dto, UpdateCategoryResponseDTO)
    assert response_dto.category_uuid == category.get_uuid()
    assert response_dto.name == request_dto.new_name
    assert response_dto.name_hy == "նոր"
    # name_ru was not part of the update request, so it stays as created.
    assert response_dto.name_ru == "старый"

    uow = await unit_of_work_provider.provide()
    async with uow:
        updated_category = await uow.category_repo.get_by_uuid(category.get_uuid())
        assert updated_category.get_name() == request_dto.new_name
        assert updated_category.get_name_hy() == "նոր"
        assert updated_category.get_name_ru() == "старый"
        await uow.commit()
