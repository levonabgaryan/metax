from uuid import uuid7

import pytest

from metax.core.application.ports.ddd_patterns.repository.errors.errors import EntityIsNotFoundError
from metax.core.domain.entities.category.value_objects import CategoryHelperWords
from metax.frameworks_and_drivers.di.metax_container import MetaxContainer
from tests.utils import make_category_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_repo_add_and_get(metax_container_for_integration_tests: MetaxContainer) -> None:
    # given
    category = make_category_entity()
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()
    # when
    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    # then
    got_category_by_uuid = await unit_of_work.category_repo.get_by_uuid(category.get_uuid())
    got_category_by_name = await unit_of_work.category_repo.get_by_name(category.get_name())

    assert got_category_by_uuid.get_uuid() == category.get_uuid()
    assert got_category_by_uuid.get_name() == category.get_name()

    assert got_category_by_name.get_uuid() == category.get_uuid()
    assert got_category_by_name.get_name() == category.get_name()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_repo_update(metax_container_for_integration_tests: MetaxContainer) -> None:
    # given
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()

    category = make_category_entity()

    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    # when
    category.set_name("test_new_name")
    async with unit_of_work as uow:
        await uow.category_repo.update(updated_category=category)
        await uow.commit()

    # then
    updated_category = await unit_of_work.category_repo.get_by_uuid(category.get_uuid())
    assert updated_category.get_name() == category.get_name()
    assert updated_category.get_helper_words() == category.get_helper_words()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_repo_update_syncs_helper_words_via_diff(
    metax_container_for_integration_tests: MetaxContainer,
) -> None:
    # given
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()
    helper_words = CategoryHelperWords.create(words=frozenset(["keep", "drop", "stay"]))
    category = make_category_entity(helper_words=helper_words)
    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    # when
    async with unit_of_work as uow:
        category = await uow.category_repo.get_by_uuid(category.get_uuid())
        category.set_helper_words(
            CategoryHelperWords.create(words=frozenset(["keep", "stay", "new_one"])),
        )
        updated_category = category
        await uow.category_repo.update(updated_category=updated_category)
        await uow.commit()

    # then
    async with unit_of_work as uow:
        testing_category = await uow.category_repo.get_by_uuid(updated_category.get_uuid())

    assert testing_category.get_helper_words() == frozenset(["keep", "stay", "new_one"])
    assert testing_category.get_name() == updated_category.get_name()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_is_not_found_by_uuid(metax_container_for_integration_tests: MetaxContainer) -> None:
    # given
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()

    random_uuid = uuid7()

    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError) as err:
            await uow.category_repo.get_by_uuid(random_uuid)

    # then
    assert err.value.title == f"There is no category entity found by field 'uuid' with value '{random_uuid}'."
    assert err.value.error_code == "CATEGORY_IS_NOT_FOUND"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_is_not_found_by_name(metax_container_for_integration_tests: MetaxContainer) -> None:
    # given
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()

    test_name = "test_name"

    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError) as err:
            await uow.category_repo.get_by_name(test_name)

    # then
    assert err.value.title == f"There is no category entity found by field 'name' with value '{test_name}'."
    assert err.value.error_code == "CATEGORY_IS_NOT_FOUND"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_update_helper_words_when_adding_news(
    metax_container_for_integration_tests: MetaxContainer,
) -> None:
    # given
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()

    helper_words = CategoryHelperWords.create(words=frozenset(["a", "b", "c"]))
    category = make_category_entity(helper_words=helper_words)
    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    # when
    async with unit_of_work as uow:
        category = await uow.category_repo.get_by_uuid(category.get_uuid())
        new_helper_words = frozenset(["d", "e"])
        category.add_new_helper_words(new_helper_words)
        await uow.category_repo.update(updated_category=category)
        await uow.commit()

    # then
    async with unit_of_work as uow:
        category = await uow.category_repo.get_by_uuid(category.get_uuid())
        assert category.get_helper_words() == frozenset(["a", "b", "c", "e", "d"])
        await uow.commit()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_update_helper_words_when_deleting(
    metax_container_for_integration_tests: MetaxContainer,
) -> None:
    # given
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()

    helper_words = CategoryHelperWords.create(words=frozenset(["a", "b", "c"]))
    category = make_category_entity(helper_words=helper_words)
    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    # when
    async with unit_of_work as uow:
        category = await uow.category_repo.get_by_uuid(category.get_uuid())
        words_to_delete = frozenset(["a", "c"])
        category.delete_helper_words(words_to_delete)
        await uow.category_repo.update(updated_category=category)
        await uow.commit()

    # then
    category = await unit_of_work.category_repo.get_by_uuid(category.get_uuid())
    assert category.get_helper_words() == frozenset(["b"])


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_repo_get_all(metax_container_for_integration_tests: MetaxContainer) -> None:
    # given
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()
    cat_alpha = make_category_entity(
        name="repo_get_all_alpha",
        helper_words=CategoryHelperWords.create(words=frozenset(["repo_ga_alpha_1", "repo_ga_alpha_2"])),
    )
    cat_beta = make_category_entity(
        name="repo_get_all_beta",
        helper_words=CategoryHelperWords.create(words=frozenset(["repo_ga_beta_1"])),
    )
    async with unit_of_work as uow:
        await uow.category_repo.add(cat_alpha)
        await uow.category_repo.add(cat_beta)
        await uow.commit()

    # when
    async with unit_of_work as uow:
        all_categories = await uow.category_repo.get_all()
        await uow.commit()

    # then
    assert sorted(all_categories, key=lambda v: v.get_uuid()) == sorted(
        [cat_alpha, cat_beta], key=lambda v: v.get_uuid()
    )
