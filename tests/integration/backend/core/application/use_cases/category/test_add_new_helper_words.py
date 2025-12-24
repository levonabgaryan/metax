import pytest

from backend.core.application.patterns.use_case_abc import UseCase, EmptyResponseDTO
from backend.core.application.ports.patterns.unit_of_work import UnitOfWork
from backend.core.application.use_cases.category.dtos import AddHelperWordsRequest
from backend.core.domain.entities.category_entity.category import CategoryHelperWords
from backend.frameworks_and_drivers.di.use_cases_container import CategoryUseCaseContainer
from tests.integration.conftest import make_category_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_add_new_helper_word_use_case(
    unit_of_work: UnitOfWork, category_use_cases: CategoryUseCaseContainer
) -> None:
    # given
    helper_words = CategoryHelperWords(words=frozenset(["a", "b"]))
    category = make_category_entity(
        helper_words=helper_words,
    )
    async with unit_of_work as uow:
        await uow.repositories.category.add(category)
        await uow.commit()

    request = AddHelperWordsRequest(category_uuid=category.get_uuid(), new_helper_words=frozenset(["c", "d"]))

    expected_helper_words = CategoryHelperWords(words=frozenset(["a", "b", "c", "d"]))
    # when
    use_case: UseCase[AddHelperWordsRequest, EmptyResponseDTO] = category_use_cases.add_new_helper_words(
        unit_of_work=unit_of_work
    )
    await use_case.execute(request)

    # then
    async with unit_of_work as uow:
        updated_category = await uow.repositories.category.get_by_uuid(category.get_uuid())
        await uow.commit()

    assert updated_category.get_helper_words() == expected_helper_words.words
