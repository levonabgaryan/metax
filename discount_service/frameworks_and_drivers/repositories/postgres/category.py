from uuid import UUID

from asgiref.sync import sync_to_async

from discount_service.core.application.ports.repositories.entites_repositories.category import (
    CategoryRepository,
    CategoryFieldsToUpdate,
)
from discount_service.core.domain.entities.category_entity.category import (
    Category,
    CategoryHelperWords,
)
from django_framework.discount_service.models.category import CategoryModel
from django_framework.discount_service.models.category_helper_words import (
    CategoryHelperWordsModel,
)


class DjangoPostgresqlCategoryRepository(CategoryRepository):
    async def _add(self, category: Category) -> None:
        category_model = await CategoryModel._default_manager.acreate(
            category_uuid=category.get_uuid(),
            name=category.get_name(),
        )

        helpers = [
            CategoryHelperWordsModel(
                word=word.lower(),
                category=category_model,
            )
            for word in category.get_helper_words()
        ]

        if helpers:
            await CategoryHelperWordsModel._default_manager.abulk_create(helpers)

    async def _get_by_uuid(self, category_uuid: UUID) -> Category | None:
        try:
            model = await CategoryModel._default_manager.prefetch_related("helper_words").aget(
                category_uuid=category_uuid
            )
        except CategoryModel.DoesNotExist:
            return None

        return await self._map_to_entity(model)

    async def _get_by_name(self, category_name: str) -> Category | None:

        try:
            model = await CategoryModel._default_manager.prefetch_related("helper_words").aget(name=category_name)
        except CategoryModel.DoesNotExist:
            return None

        return await self._map_to_entity(model)

    async def _update(
        self,
        updated_category: Category,
        fields_to_update: CategoryFieldsToUpdate,
    ) -> None:

        data = {}

        if fields_to_update.name:
            data["name"] = updated_category.get_name()

        if not data:
            return

        await CategoryModel._default_manager.filter(category_uuid=updated_category.get_uuid()).aupdate(**data)

    async def _update_helper_words(self, updated_category: Category) -> None:

        updated_words = list(updated_category.get_helper_words())

        await (
            CategoryHelperWordsModel._default_manager.filter(category_id=updated_category.get_uuid())
            .exclude(word__in=updated_words)
            .adelete()
        )

        to_create = [
            CategoryHelperWordsModel(
                word=word,
                category_id=updated_category.get_uuid(),
            )
            for word in updated_words
        ]

        if to_create:
            await CategoryHelperWordsModel._default_manager.abulk_create(
                to_create,
                ignore_conflicts=True,
            )

    @staticmethod
    def _map_to_entity_sync(model: CategoryModel) -> Category:
        words = frozenset(hw.word for hw in model.helper_words.all())
        return Category(
            category_uuid=model.category_uuid,
            name=model.name,
            helper_words=CategoryHelperWords(words=words),
        )

    async def _map_to_entity(self, model: CategoryModel) -> Category:
        return await sync_to_async(self._map_to_entity_sync)(model)

    async def _get_by_helper_words_in_words(
        self,
        words: list[str],
    ) -> Category | None:
        helper = await (
            CategoryHelperWordsModel._default_manager.select_related("category")
            .prefetch_related("category__helper_words")
            .filter(word__in=words)
            .afirst()
        )

        if not helper or not helper.category:
            return None

        return await self._map_to_entity(helper.category)

    async def get_all(self) -> list[Category]:
        qs = CategoryModel._default_manager.prefetch_related("helper_words").all()
        categories = []

        async for model in qs.aiterator():
            categories.append(await self._map_to_entity(model))

        return categories
