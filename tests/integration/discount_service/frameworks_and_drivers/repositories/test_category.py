from uuid import uuid4

import pytest
from dependency_injector.wiring import inject, Provide

from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.core.application.ports.repositories.entites_repositories.category import (
    CategoryFieldsToUpdate,
)
from discount_service.core.application.ports.repositories.errors.errors import EntityIsNotFoundError
from discount_service.core.domain.entities.category_entity.category import (
    CategoryHelperWords,
    DataForCategoryUpdate,
)
from discount_service.frameworks_and_drivers.di.boostrap import ServiceContainer
from tests.utils import make_category_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@inject
async def test_category_repo_add_and_get(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
) -> None:
    # given
    category = make_category_entity()

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
@inject
async def test_category_repo_update(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
) -> None:
    # given
    category = make_category_entity()

    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    new_data = DataForCategoryUpdate(new_name="test_new_name")
    fields_to_update = CategoryFieldsToUpdate(name=True)
    # when
    category.update(new_data)
    async with unit_of_work as uow:
        await uow.category_repo.update(updated_category=category, fields_to_update=fields_to_update)
        await uow.commit()

    # then
    updated_category = await unit_of_work.category_repo.get_by_uuid(category.get_uuid())
    assert updated_category.get_name() == category.get_name()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@inject
async def test_category_is_not_found_by_uuid(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
) -> None:
    # given
    random_uuid = uuid4()
    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError) as err:
            await uow.category_repo.get_by_uuid(random_uuid)

    # then
    assert err.value.message == f"There is no category entity found by field 'uuid' with value '{random_uuid}'."
    assert err.value.error_code == "CATEGORY_IS_NOT_FOUND"
    assert err.value.details == {"searched_field_name": "uuid", "searched_field_value": f"{random_uuid}"}


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@inject
async def test_category_is_not_found_by_name(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
) -> None:
    # given
    test_name = "test_name"

    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError) as err:
            await uow.category_repo.get_by_name(test_name)

    # then
    assert err.value.message == f"There is no category entity found by field 'name' with value '{test_name}'."
    assert err.value.error_code == "CATEGORY_IS_NOT_FOUND"
    assert err.value.details == {"searched_field_name": "name", "searched_field_value": f"{test_name}"}


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@inject
async def test_category_update_helper_words_when_adding_news(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
) -> None:
    # given
    helper_words = CategoryHelperWords(words=frozenset(["a", "b", "c"]))
    category = make_category_entity(helper_words=helper_words)
    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    # when
    async with unit_of_work as uow:
        category = await uow.category_repo.get_by_uuid(category.get_uuid())
        new_helper_words = frozenset(["d", "e"])
        category.add_new_helper_words(new_helper_words)
        await uow.category_repo.update_helper_words(category)
        await uow.commit()

    # then
    async with unit_of_work as uow:
        category = await uow.category_repo.get_by_uuid(category.get_uuid())
        assert category.get_helper_words() == frozenset(["a", "b", "c", "e", "d"])
        await uow.commit()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@inject
async def test_category_update_helper_words_when_deleting(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
) -> None:
    # given
    helper_words = CategoryHelperWords(words=frozenset(["a", "b", "c"]))
    category = make_category_entity(helper_words=helper_words)
    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    # when
    async with unit_of_work as uow:
        category = await uow.category_repo.get_by_uuid(category.get_uuid())
        words_to_delete = frozenset(["a", "c"])
        category.delete_helper_words(words_to_delete)
        await uow.category_repo.update_helper_words(category)
        await uow.commit()

    # then
    category = await unit_of_work.category_repo.get_by_uuid(category.get_uuid())
    assert category.get_helper_words() == frozenset(["b"])
    await uow.commit()
