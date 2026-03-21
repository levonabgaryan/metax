from typing import override
from uuid import UUID

from asgiref.sync import sync_to_async
from django.db.models import QuerySet

from metax.core.application.ports.repositories.entites_repositories.category import (
    CategoryRepository,
    CategoryFieldsToUpdate,
)
from metax.core.domain.entities.category_entity.category import (
    Category,
    CategoryHelperWords,
)
from django_framework.metax.models.category import CategoryModel
from django_framework.metax.models.category_helper_words import (
    CategoryHelperWordsModel,
)


class DjangoPostgresqlCategoryRepository(CategoryRepository):
    @override
    async def _add(self, category: Category) -> None:
        category_model = await CategoryModel._default_manager.acreate(
            category_uuid=category.get_uuid(), name=category.get_name()
        )
        helper_words_models_to_create = []
        for helper_word in category.get_helper_words():
            helper_words_models_to_create.append(
                CategoryHelperWordsModel(word=helper_word, category=category_model)
            )

        if helper_words_models_to_create:
            await CategoryHelperWordsModel._default_manager.abulk_create(helper_words_models_to_create)

    @override
    async def _get_by_uuid(self, category_uuid: UUID) -> Category | None:
        try:
            category_model = await CategoryModel._default_manager.aget(category_uuid=category_uuid)
        except CategoryModel.DoesNotExist:
            return None

        return await self.__map_to_entity(model=category_model)

    @override
    async def _get_by_name(self, category_name: str) -> Category | None:
        try:
            category_model = await CategoryModel._default_manager.aget(name=category_name)
        except CategoryModel.DoesNotExist:
            return None

        return await self.__map_to_entity(model=category_model)

    @override
    async def _update(self, updated_category: Category, fields_to_update: CategoryFieldsToUpdate) -> None:
        update_data = {}

        if fields_to_update.name:
            update_data["name"] = updated_category.get_name()

        if not update_data:
            return

        await CategoryModel._default_manager.filter(category_uuid=updated_category.get_uuid()).aupdate(
            **update_data
        )

    @override
    async def _update_helper_words(self, updated_category: Category) -> None:
        updated_words = list(updated_category.get_helper_words())

        await (
            CategoryHelperWordsModel._default_manager.filter(category_id=updated_category.get_uuid())
            .exclude(word__in=updated_words)
            .adelete()
        )
        to_create = [
            CategoryHelperWordsModel(word=word, category_id=updated_category.get_uuid()) for word in updated_words
        ]
        if to_create:
            await CategoryHelperWordsModel._default_manager.abulk_create(to_create, ignore_conflicts=True)

    @sync_to_async(thread_sensitive=True)
    def __get_helper_words_by_category_uuid(self, category_uuid: UUID) -> frozenset[str]:
        helper_words: QuerySet[CategoryHelperWordsModel, str] = CategoryHelperWordsModel._default_manager.filter(
            category_id=category_uuid
        ).values_list("word", flat=True)
        return frozenset(helper_words)

    async def __map_to_entity(self, model: CategoryModel) -> Category:
        category_uuid = model.category_uuid
        helper_words = await self.__get_helper_words_by_category_uuid(category_uuid)

        return Category(
            category_uuid=category_uuid, name=model.name, helper_words=CategoryHelperWords(words=helper_words)
        )

    @override
    async def get_all(self) -> list[Category]:
        categories: list[Category] = []
        async for model in CategoryModel.objects.all():
            entity = await self.__map_to_entity(model)
            categories.append(entity)
        return categories

    @override
    async def _get_by_helper_words_in_words(self, words: list[str]) -> Category | None:
        helper_word_model = (
            await CategoryHelperWordsModel.objects.select_related("category").filter(word__in=words).afirst()
        )

        if not helper_word_model:
            return None

        return await self.__map_to_entity(helper_word_model.category)
