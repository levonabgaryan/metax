import pytest

from metax.core.application.cud_services.category import (
    DeleteHelperWordRequestDTO,
    DeleteHelperWordResponseDTO,
    DeleteHelperWordService,
)
from metax_lifespan import MetaxAppLifespanManager
from tests.utils import make_category_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_delete_helper_word_service(
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

    helper_word_uuid_to_delete = next(
        helper_word.get_uuid()
        for helper_word in category.get_helper_words()
        if helper_word.get_helper_word_text() == "test_word1"
    )
    request_dto = DeleteHelperWordRequestDTO(
        category_uuid=category.get_uuid(),
        helper_word_uuid=helper_word_uuid_to_delete,
    )

    # when
    service = DeleteHelperWordService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
    response_dto = await service.execute(request_dto)

    # then
    assert isinstance(response_dto, DeleteHelperWordResponseDTO)
    assert response_dto.category_uuid == category.get_uuid()
    assert response_dto.deleted_helper_word_payload.helper_word_uuid == helper_word_uuid_to_delete
    assert response_dto.deleted_helper_word_payload.helper_word_text == "test_word1"

    async with unit_of_work as uow:
        updated_category = await uow.category_repo.get_by_uuid(category.get_uuid())

    assert {word.get_helper_word_text() for word in updated_category.get_helper_words()} == {"test_word2"}
