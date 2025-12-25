import pytest

from backend.core.application.ports.patterns.unit_of_work import UnitOfWork
from backend.core.domain.entities.category_entity.category import CategoryHelperWords
from backend.interface_adapters.controllers.category import CategoryController
from tests.integration.conftest import make_category_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_controller_create(
    unit_of_work: UnitOfWork, category_controller: CategoryController
) -> None:
    # given
    category_name = "test_name"
    helper_words = frozenset(["a", "b", "c"])

    # when
    await category_controller.create(name=category_name, helper_words=helper_words)

    # then
    async with unit_of_work as uow:
        category = await uow.repositories.category.get_by_name(category_name)
        await uow.commit()

    assert category.get_name() == category_name
    assert category.get_helper_words() == helper_words


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_controller_update(
    unit_of_work: UnitOfWork, category_controller: CategoryController
) -> None:
    # given
    category = make_category_entity()

    async with unit_of_work as uow:
        await uow.repositories.category.add(category)
        await uow.commit()

    new_name = "new_name"

    # when
    await category_controller.update(category_uuid=str(category.get_uuid()), new_name=new_name)

    # then
    async with unit_of_work as uow:
        category = await uow.repositories.category.get_by_uuid(category.get_uuid())
        await uow.commit()

    assert category.get_name() == category.get_name()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_controller_add_new_helper_words(
    unit_of_work: UnitOfWork, category_controller: CategoryController
) -> None:
    # given
    helper_words = CategoryHelperWords(words=frozenset(["a", "b", "c"]))

    category = make_category_entity(helper_words=helper_words)
    new_words = frozenset(["d"])
    expected_new_words = frozenset(["a", "b", "d", "c"])

    async with unit_of_work as uow:
        await uow.repositories.category.add(category)
        await uow.commit()

    # when
    await category_controller.add_new_helper_words(category_uuid=str(category.get_uuid()), new_words=new_words)

    # then
    async with unit_of_work as uow:
        updated_category = await uow.repositories.category.get_by_uuid(category.get_uuid())
        await uow.commit()

    assert updated_category.get_helper_words() == expected_new_words


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_controller_delete_helper_words(
    unit_of_work: UnitOfWork, category_controller: CategoryController
) -> None:
    helper_words = CategoryHelperWords(words=frozenset(["a", "b", "c"]))
    category = make_category_entity(helper_words=helper_words)

    words_to_delete = frozenset(["a", "b"])
    expected_words = frozenset(["c"])

    async with unit_of_work as uow:
        await uow.repositories.category.add(category)
        await uow.commit()

    # when
    await category_controller.delete_helper_words(
        category_uuid=str(category.get_uuid()), words_to_delete=words_to_delete
    )

    # then
    async with unit_of_work as uow:
        updated_category = await uow.repositories.category.get_by_uuid(category.get_uuid())
        await uow.commit()
    assert updated_category.get_helper_words() == expected_words
