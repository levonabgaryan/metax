from uuid import uuid7

import pytest

from constants import ErrorCodes
from metax.core.application.ports.ddd_patterns.repository.errors import (
    EntityAlreadyExistsError,
    EntityIsNotFoundError,
)
from metax_lifespan import MetaxAppLifespanManager
from tests.utils import make_category_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_repo_add_and_get(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    metax_container = metax_lifespan_manager_for_tests.get_metax_container()
    category = make_category_entity(name_hy="կաթ", name_ru="молоко")
    unit_of_work = metax_container.get_unit_of_work()

    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    got_by_uuid = await unit_of_work.category_repo.get_by_uuid(category.get_uuid())
    got_by_name = await unit_of_work.category_repo.get_by_name(category.get_name())

    assert got_by_uuid.get_uuid() == category.get_uuid()
    assert got_by_uuid.get_name() == category.get_name()
    assert got_by_uuid.get_name_hy() == "կաթ"
    assert got_by_uuid.get_name_ru() == "молоко"
    assert got_by_name.get_uuid() == category.get_uuid()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_repo_update_name(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    metax_container = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work = metax_container.get_unit_of_work()
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
async def test_category_is_not_found_by_uuid(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work = metax_container.get_unit_of_work()
    random_uuid = uuid7()

    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError):
            await uow.category_repo.get_by_uuid(random_uuid)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_is_not_found_by_name(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work = metax_container.get_unit_of_work()

    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError):
            await uow.category_repo.get_by_name("unknown_category")


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_repo_list_paginated_returns_full_entities(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work = metax_container.get_unit_of_work()
    category_a = make_category_entity(name="A")
    category_b = make_category_entity(name="B")
    category_c = make_category_entity(name="C")
    category_d = make_category_entity(name="D")

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


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_repo_delete_by_uuid(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work = metax_container.get_unit_of_work()
    category = make_category_entity()

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


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_repo_delete_by_uuid_not_found(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work = metax_container.get_unit_of_work()
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
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work = metax_container.get_unit_of_work()
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
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work = metax_container.get_unit_of_work()
    category_a = make_category_entity(name="category-a-unique")
    category_b = make_category_entity(name="category-b-unique")

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


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_category_repo_loads_keywords_and_update_does_not_clobber_them(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
) -> None:
    # given: keywords are curated in the admin, outside the entity-update path
    unit_of_work = metax_lifespan_manager_for_tests.get_metax_container().get_unit_of_work()
    category = make_category_entity()
    category.set_keywords(["պանիր", "միցելային ջուր"])
    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.commit()

    # when: the name is updated through the domain service path
    category.set_name("renamed")
    async with unit_of_work as uow:
        await uow.category_repo.update(updated_category=category)
        await uow.commit()

    # then
    loaded = await unit_of_work.category_repo.get_by_uuid(category.get_uuid())
    assert loaded.get_keywords() == ["պանիր", "միցելային ջուր"]
    assert [
        c.get_keywords() for c in await unit_of_work.category_repo.all() if c.get_uuid() == category.get_uuid()
    ] == [["պանիր", "միցելային ջուր"]]


@pytest.mark.django_db(transaction=True)
def test_admin_form_rejects_a_keyword_owned_by_another_category() -> None:
    from django_framework.metax.admin.category import CategoryAdminForm
    from django_framework.metax.models import CategoryModel

    # given
    CategoryModel.objects.create(uuid=uuid7(), name="Groceries", keywords="պանիր\nկաթ")

    # when: another category claims «Պանիր» (case and spacing don't matter)
    form = CategoryAdminForm(
        data={"name": "Dairy", "name_hy": "", "name_ru": "", "examples": "", "keywords": " Պանիր\nմածուն"}
    )

    # then
    assert not form.is_valid()
    assert "պանիր" in form.errors["keywords"][0]
    assert "Groceries" in form.errors["keywords"][0]


@pytest.mark.django_db(transaction=True)
def test_admin_form_accepts_unique_keywords() -> None:
    from django_framework.metax.admin.category import CategoryAdminForm
    from django_framework.metax.models import CategoryModel

    CategoryModel.objects.create(uuid=uuid7(), name="Groceries", keywords="պանիր")
    form = CategoryAdminForm(
        data={"name": "Drinks", "name_hy": "", "name_ru": "", "examples": "", "keywords": "ջուր"}
    )

    assert form.is_valid(), form.errors
