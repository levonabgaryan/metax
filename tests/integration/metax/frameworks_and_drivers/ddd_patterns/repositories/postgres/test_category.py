from uuid import uuid7

import pytest

from metax.core.application.ports.ddd_patterns.repository.errors import EntityIsNotFoundError
from metax.core.domain.entities.category_helper_word.entity import CategoryHelperWord
from metax_lifespan import MetaxAppLifespanManager
from tests.utils import make_category_entity


def _make_helper_word(text: str) -> CategoryHelperWord:
    category = make_category_entity()
    first = category.get_helper_words()[0]
    return CategoryHelperWord(
        uuid_=uuid7(),
        text=text,
        created_at=first.get_created_at(),
        updated_at=first.get_updated_at(),
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_repo_add_and_get(metax_app_for_integration_tests: MetaxAppLifespanManager) -> None:
    metax_container = metax_app_for_integration_tests.get_di_container()
    category = make_category_entity()
    unit_of_work = metax_container.patterns_container.container.unit_of_work()

    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    got_by_uuid = await unit_of_work.category_repo.get_by_uuid(category.get_uuid())
    got_by_name = await unit_of_work.category_repo.get_by_name(category.get_name())

    assert got_by_uuid.get_uuid() == category.get_uuid()
    assert got_by_uuid.get_name() == category.get_name()
    assert {word.get_text() for word in got_by_uuid.get_helper_words()} == {
        word.get_text() for word in category.get_helper_words()
    }
    assert got_by_name.get_uuid() == category.get_uuid()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_repo_update_name(metax_app_for_integration_tests: MetaxAppLifespanManager) -> None:
    metax_container = metax_app_for_integration_tests.get_di_container()
    unit_of_work = metax_container.patterns_container.container.unit_of_work()
    category = make_category_entity()

    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    category.set_name("test_new_name")
    async with unit_of_work as uow:
        await uow.category_repo.update(updated_category=category)
        await uow.commit()

    updated_category = await unit_of_work.category_repo.get_by_uuid(category.get_uuid())
    assert updated_category.get_name() == "test_new_name"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_repo_update_helper_words_via_diff(
    metax_app_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    metax_container = metax_app_for_integration_tests.get_di_container()
    unit_of_work = metax_container.patterns_container.container.unit_of_work()
    category = make_category_entity()

    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    loaded_category = await unit_of_work.category_repo.get_by_uuid(category.get_uuid())
    loaded_helper_words = loaded_category.get_helper_words()
    loaded_category.update_helper_word_text_by_uuid(
        helper_word_uuid=loaded_helper_words[0].get_uuid(),
        text="updated_word",
    )
    loaded_category.delete_helper_words_by_uuids(
        [loaded_helper_words[1].get_uuid()],
    )
    loaded_category.add_new_helper_words([_make_helper_word("new_word")])

    async with unit_of_work as uow:
        await uow.category_repo.update(updated_category=loaded_category)
        await uow.commit()

    testing_category = await unit_of_work.category_repo.get_by_uuid(loaded_category.get_uuid())
    assert {word.get_text() for word in testing_category.get_helper_words()} == {
        "updated_word",
        "new_word",
    }


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_is_not_found_by_uuid(metax_app_for_integration_tests: MetaxAppLifespanManager) -> None:
    metax_container = metax_app_for_integration_tests.get_di_container()
    unit_of_work = metax_container.patterns_container.container.unit_of_work()
    random_uuid = uuid7()

    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError):
            await uow.category_repo.get_by_uuid(random_uuid)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_is_not_found_by_name(metax_app_for_integration_tests: MetaxAppLifespanManager) -> None:
    metax_container = metax_app_for_integration_tests.get_di_container()
    unit_of_work = metax_container.patterns_container.container.unit_of_work()

    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError):
            await uow.category_repo.get_by_name("unknown_category")
