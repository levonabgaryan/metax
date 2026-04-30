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
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_integration_tests.get_di_container()
    unit_of_work_provider = (
        metax_container_for_integration_tests.patterns_container.container.unit_of_work_provider()
    )
    event_bus = await metax_container_for_integration_tests.resources_container.container.event_bus.async_()
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()
    category = make_category_entity()

    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    initial_helper_words = category.get_helper_words()

    # when
    request_dto = UpdateCategoryRequestDTO(category_uuid=category.get_uuid(), new_name="new_test_name")
    service = UpdateCategoryService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
    response_dto = await service.execute(request_dto)

    # then
    assert isinstance(response_dto, UpdateCategoryResponseDTO)
    assert response_dto.category_uuid == category.get_uuid()
    assert response_dto.name == request_dto.new_name
    assert {word.helper_word_text for word in response_dto.helper_words_payload} == {
        word.get_helper_word_text() for word in initial_helper_words
    }

    uow = await unit_of_work_provider.provide()
    async with uow:
        updated_category = await uow.category_repo.get_by_uuid(category.get_uuid())
        assert updated_category.get_name() == request_dto.new_name
        assert updated_category.get_helper_words() == initial_helper_words
        await uow.commit()
