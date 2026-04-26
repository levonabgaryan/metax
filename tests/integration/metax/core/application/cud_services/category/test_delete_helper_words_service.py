import pytest

from metax.core.application.cud_services.category import (
    DeleteHelperWordsRequestDTO,
    DeleteHelperWordsResponseDTO,
    DeleteHelperWordsService,
)
from metax_lifespan import MetaxAppLifespanManager
from tests.utils import make_category_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_delete_helper_words_service(
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

    words_to_delete_uuids = [
        helper_word.get_uuid()
        for helper_word in category.get_helper_words()
        if helper_word.get_text() in {"test_word1"}
    ]
    request_dto = DeleteHelperWordsRequestDTO(
        category_uuid=category.get_uuid(),
        helper_words_uuid=words_to_delete_uuids,
    )

    # when
    service = DeleteHelperWordsService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
    response_dto = await service.execute(request_dto)

    # then
    assert isinstance(response_dto, DeleteHelperWordsResponseDTO)
    assert response_dto.category_uuid == category.get_uuid()
    assert {word.text for word in response_dto.helper_words_payload} == {"test_word2"}

    async with unit_of_work as uow:
        updated_category = await uow.category_repo.get_by_uuid(category.get_uuid())

    assert {word.get_text() for word in updated_category.get_helper_words()} == {"test_word2"}
