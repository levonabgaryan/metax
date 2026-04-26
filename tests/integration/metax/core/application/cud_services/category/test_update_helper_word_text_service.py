import pytest

from metax.core.application.cud_services.category import (
    UpdateHelperWordTextRequestDTO,
    UpdateHelperWordTextResponseDTO,
    UpdateHelperWordTextService,
)
from metax_lifespan import MetaxAppLifespanManager
from tests.utils import make_category_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_helper_word_text_service(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_integration_tests.get_di_container()
    unit_of_work_provider = (
        metax_container_for_integration_tests.patterns_container.container.unit_of_work_provider()
    )
    event_bus = await metax_container_for_integration_tests.patterns_container.container.event_bus.async_()
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()
    category = make_category_entity()

    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    helper_word_to_update = category.get_helper_words()[0]
    helper_word_to_keep = category.get_helper_words()[1]
    request_dto = UpdateHelperWordTextRequestDTO(
        category_uuid=category.get_uuid(),
        helper_word_uuid=helper_word_to_update.get_uuid(),
        new_text="updated_helper_word_text",
    )

    # when
    service = UpdateHelperWordTextService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
    response_dto = await service.execute(request_dto)

    # then
    assert isinstance(response_dto, UpdateHelperWordTextResponseDTO)
    assert response_dto.category_uuid == category.get_uuid()
    assert response_dto.name == category.get_name()
    assert {word.text for word in response_dto.helper_words_payload} == {
        "updated_helper_word_text",
        helper_word_to_keep.get_text(),
    }

    uow = await unit_of_work_provider.provide()
    async with uow:
        updated_category = await uow.category_repo.get_by_uuid(category.get_uuid())
        updated_words = {word.get_text() for word in updated_category.get_helper_words()}
        assert updated_category.get_name() == category.get_name()
        assert updated_words == {"updated_helper_word_text", helper_word_to_keep.get_text()}
        await uow.commit()
