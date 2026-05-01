from uuid import uuid7

import pytest

from constants import ErrorCodes
from metax.core.application.ports.ddd_patterns.repository.errors import (
    EntityAlreadyExistsError,
    EntityIsNotFoundError,
)
from metax.core.domain.entities.category_helper_word.entity import CategoryHelperWord
from metax_lifespan import MetaxAppLifespanManager
from tests.utils import make_category_entity


def _make_helper_word(text: str) -> CategoryHelperWord:
    category = make_category_entity()
    first = category.get_helper_words()[0]
    return CategoryHelperWord(
        uuid_=uuid7(),
        helper_word_text=text,
        created_at=first.get_created_at(),
        updated_at=first.get_updated_at(),
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_repo_add_and_get(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    metax_container = metax_lifespan_manager_for_integration_tests.get_di_container()
    category = make_category_entity()
    unit_of_work = metax_container.patterns_container.container.unit_of_work()

    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    got_by_uuid = await unit_of_work.category_repo.get_by_uuid(category.get_uuid())
    got_by_name = await unit_of_work.category_repo.get_by_name(category.get_name())

    assert got_by_uuid.get_uuid() == category.get_uuid()
    assert got_by_uuid.get_name() == category.get_name()
    assert {word.get_helper_word_text() for word in got_by_uuid.get_helper_words()} == {
        word.get_helper_word_text() for word in category.get_helper_words()
    }
    assert got_by_name.get_uuid() == category.get_uuid()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_repo_update_name(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    metax_container = metax_lifespan_manager_for_integration_tests.get_di_container()
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
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_integration_tests.get_di_container()
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
    # when
    loaded_category.add_new_helper_words([_make_helper_word("new_word")])

    async with unit_of_work as uow:
        await uow.category_repo.update(updated_category=loaded_category)
        await uow.commit()

    # then
    testing_category = await unit_of_work.category_repo.get_by_uuid(loaded_category.get_uuid())
    assert {word.get_helper_word_text() for word in testing_category.get_helper_words()} == {
        "updated_word",
        "new_word",
    }


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_is_not_found_by_uuid(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_integration_tests.get_di_container()
    unit_of_work = metax_container.patterns_container.container.unit_of_work()
    random_uuid = uuid7()

    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError):
            await uow.category_repo.get_by_uuid(random_uuid)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_is_not_found_by_name(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_integration_tests.get_di_container()
    unit_of_work = metax_container.patterns_container.container.unit_of_work()

    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError):
            await uow.category_repo.get_by_name("unknown_category")


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_repo_list_paginated_returns_full_entities(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_integration_tests.get_di_container()
    unit_of_work = metax_container.patterns_container.container.unit_of_work()
    category_a = make_category_entity(
        name="A",
        helper_words=[
            _make_helper_word("a-word-1"),
            _make_helper_word("a-word-2"),
            _make_helper_word("a-word-3"),
        ],
    )
    category_b = make_category_entity(name="B", helper_words=[_make_helper_word("b-word-1")])
    category_c = make_category_entity(name="C", helper_words=[_make_helper_word("c-word-1")])
    category_d = make_category_entity(name="D", helper_words=[_make_helper_word("d-word-1")])

    async with unit_of_work as uow:
        await uow.category_repo.add(category_a)
        await uow.category_repo.add(category_b)
        await uow.category_repo.add(category_c)
        await uow.category_repo.add(category_d)
        await uow.commit()

    # when
    total_count_1, first_page = await unit_of_work.category_repo.list_paginated_and_total_count(limit=2, offset=0)
    total_count_2, second_page = await unit_of_work.category_repo.list_paginated_and_total_count(limit=2, offset=2)

    # then
    assert total_count_1 == total_count_2 == 4
    assert [category.get_name() for category in first_page] == ["A", "B"]
    assert [category.get_name() for category in second_page] == ["C", "D"]
    assert {word.get_helper_word_text() for word in first_page[0].get_helper_words()} == {
        "a-word-1",
        "a-word-2",
        "a-word-3",
    }
    assert {word.get_helper_word_text() for word in first_page[1].get_helper_words()} == {"b-word-1"}
    assert {word.get_helper_word_text() for word in second_page[0].get_helper_words()} == {"c-word-1"}
    assert {word.get_helper_word_text() for word in second_page[1].get_helper_words()} == {"d-word-1"}


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_repo_get_by_helper_word_uuid(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_integration_tests.get_di_container()
    unit_of_work = metax_container.patterns_container.container.unit_of_work()
    category = make_category_entity()
    helper_word_uuid = category.get_helper_words()[0].get_uuid()

    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    # when
    found_category = await unit_of_work.category_repo.get_by_helper_word_uuid(helper_word_uuid=helper_word_uuid)

    # then
    assert found_category.get_uuid() == category.get_uuid()
    assert found_category.get_name() == category.get_name()
    assert {word.get_helper_word_text() for word in found_category.get_helper_words()} == {
        word.get_helper_word_text() for word in category.get_helper_words()
    }


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_is_not_found_by_helper_word_uuid(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_integration_tests.get_di_container()
    unit_of_work = metax_container.patterns_container.container.unit_of_work()

    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError):
            await uow.category_repo.get_by_helper_word_uuid(helper_word_uuid=uuid7())


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_repo_delete_by_uuid(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_integration_tests.get_di_container()
    unit_of_work = metax_container.patterns_container.container.unit_of_work()
    category = make_category_entity()
    helper_word_uuids = [helper_word.get_uuid() for helper_word in category.get_helper_words()]

    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    # when
    async with unit_of_work as uow:
        await uow.category_repo.delete_by_uuid(category.get_uuid())
        await uow.commit()

    # then
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError):
            await uow.category_repo.get_by_uuid(category.get_uuid())
        for helper_word_uuid in helper_word_uuids:
            with pytest.raises(EntityIsNotFoundError):
                await uow.category_repo.get_by_helper_word_uuid(helper_word_uuid=helper_word_uuid)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_repo_delete_by_uuid_not_found(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_integration_tests.get_di_container()
    unit_of_work = metax_container.patterns_container.container.unit_of_work()
    random_uuid = uuid7()

    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError) as err:
            await uow.category_repo.delete_by_uuid(random_uuid)

    # then
    assert err.value.title == "category not found."
    assert err.value.details == f"No category found by 'uuid' = '{random_uuid}'."
    assert err.value.error_code == ErrorCodes.ENTITY_IS_NOT_FOUND


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_repo_add_duplicate_name_raises_entity_already_exists(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_integration_tests.get_di_container()
    unit_of_work = metax_container.patterns_container.container.unit_of_work()
    existing = make_category_entity(name="duplicate-category-name")
    duplicate_name = make_category_entity(name="duplicate-category-name")

    async with unit_of_work as uow:
        await uow.category_repo.add(existing)
        await uow.commit()

    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityAlreadyExistsError) as err:
            await uow.category_repo.add(duplicate_name)

    # then
    assert err.value.error_code == ErrorCodes.ENTITY_ALREADY_EXISTS
    assert err.value.title == "category already exists."
    assert err.value.details == "An existing category was found by 'name' = 'duplicate-category-name'."


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_repo_update_duplicate_name_raises_entity_already_exists(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_integration_tests.get_di_container()
    unit_of_work = metax_container.patterns_container.container.unit_of_work()
    category_a = make_category_entity(
        name="category-a-unique",
        helper_words=[_make_helper_word("category-a-word-1"), _make_helper_word("category-a-word-2")],
    )
    category_b = make_category_entity(
        name="category-b-unique",
        helper_words=[_make_helper_word("category-b-word-1"), _make_helper_word("category-b-word-2")],
    )

    async with unit_of_work as uow:
        await uow.category_repo.add(category_a)
        await uow.category_repo.add(category_b)
        await uow.commit()

    # expect
    category_b.set_name(category_a.get_name())
    async with unit_of_work as uow:
        with pytest.raises(EntityAlreadyExistsError) as err:
            await uow.category_repo.update(category_b)

    # then
    assert err.value.error_code == ErrorCodes.ENTITY_ALREADY_EXISTS
    assert err.value.title == "category already exists."
    assert err.value.details == "An existing category was found by 'name' = 'category-a-unique'."
