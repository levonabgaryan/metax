import pytest

from metax.core.application.cud_services.category import (
    AddNewHelperWordsRequestDTO,
    AddNewHelperWordsResponseDTO,
    AddNewHelperWordsService,
)
from metax.core.application.cud_services.category.dtos import HelperWordPayloadRequestDTO
from metax_lifespan import MetaxAppLifespanManager
from tests.utils import make_category_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_add_new_helper_words_service(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_integration_tests.get_metax_container()
    unit_of_work_provider = metax_container.get_unit_of_work_provider()
    event_bus = await metax_container.get_event_bus()
    unit_of_work = metax_container.get_unit_of_work()
    category = make_category_entity()
    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    request_dto = AddNewHelperWordsRequestDTO(
        category_uuid=category.get_uuid(),
        new_helper_word_payload=HelperWordPayloadRequestDTO(helper_word_text="c"),
    )
    # when
    service = AddNewHelperWordsService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
    response_dto = await service.execute(request_dto)

    # then
    assert isinstance(response_dto, AddNewHelperWordsResponseDTO)
    assert response_dto.category_uuid == category.get_uuid()
    assert response_dto.new_helper_word_payload.helper_word_text == "c"

    async with unit_of_work as uow:
        updated_category = await uow.category_repo.get_by_uuid(category.get_uuid())

    assert {word.get_helper_word_text() for word in updated_category.get_helper_words()} == {
        "test_word1",
        "test_word2",
        "c",
    }
