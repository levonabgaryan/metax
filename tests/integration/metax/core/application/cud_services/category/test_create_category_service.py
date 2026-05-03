import pytest

from metax.core.application.cud_services.category import (
    CreateCategoryRequestDTO,
    CreateCategoryResponseDTO,
    CreateCategoryService,
    HelperWordPayloadRequestDTO,
)
from metax_lifespan import MetaxAppLifespanManager


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_create_category_service(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_integration_tests.get_metax_container()
    unit_of_work_provider = metax_container.get_unit_of_work_provider()
    event_bus = await metax_container.get_event_bus()
    request_dto = CreateCategoryRequestDTO(
        name="Test Category",
        helper_words_payload=[
            HelperWordPayloadRequestDTO(helper_word_text="A"),
            HelperWordPayloadRequestDTO(helper_word_text="B"),
        ],
    )

    # when
    service = CreateCategoryService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
    response_dto = await service.execute(request_dto)

    # then
    assert isinstance(response_dto, CreateCategoryResponseDTO)
    assert response_dto.name == request_dto.name
    assert {word.helper_word_text for word in response_dto.helper_words_payload} == {"A", "B"}

    uow = await unit_of_work_provider.provide()
    async with uow:
        category = await uow.category_repo.get_by_uuid(response_dto.category_uuid)
    assert category.get_uuid() == response_dto.category_uuid
    assert category.get_name() == request_dto.name
    assert {word.get_helper_word_text() for word in category.get_helper_words()} == {"B", "A"}


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_create_category_service_without_helper_words(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_integration_tests.get_metax_container()
    unit_of_work_provider = metax_container.get_unit_of_work_provider()
    event_bus = await metax_container.get_event_bus()
    request_dto = CreateCategoryRequestDTO(
        name="Category Without Helper Words",
    )

    # when
    service = CreateCategoryService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
    response_dto = await service.execute(request_dto)

    # then
    assert isinstance(response_dto, CreateCategoryResponseDTO)
    assert response_dto.name == request_dto.name
    assert response_dto.helper_words_payload == []

    uow = await unit_of_work_provider.provide()
    async with uow:
        category = await uow.category_repo.get_by_uuid(response_dto.category_uuid)
        await uow.commit()
    assert category.get_uuid() == response_dto.category_uuid
    assert category.get_name() == request_dto.name
    assert category.get_helper_words() == []
