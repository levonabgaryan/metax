from typing import override
from uuid import UUID

from asgiref.sync import sync_to_async
from django.db import connection
from django.db.backends.utils import CursorWrapper
from django.db.models import QuerySet
from django_framework.metax.models.category import CategoryModel
from django_framework.metax.models.category_helper_words import (
    CategoryHelperWordsModel,
)

from metax.core.application.ports.ddd_patterns.repository.entites_repositories.category import (
    CategoryRepository,
)
from metax.core.domain.entities.category.entity import (
    Category,
)
from metax.core.domain.entities.category.value_objects import CategoryHelperWords


class DjangoPostgresqlCategoryRepository(CategoryRepository):
    @override
    async def _add(self, category: Category) -> None:
        def _sync_version(_category: Category) -> None:
            _category_insert_query = """
                INSERT INTO categories (category_uuid, name)
                VALUES (%s, %s);
            """
            _cursor: CursorWrapper
            with connection.cursor() as _cursor:
                _cursor.execute(sql=_category_insert_query, params=[_category.get_uuid(), _category.get_name()])

                _words = list(_category.get_helper_words())
                if _words:
                    helper_words_insert_query = """
                        INSERT INTO category_helper_words (category_uuid, word)
                        VALUES (%s, %s);
                    """
                    _params = [(_category.get_uuid(), word) for word in _words]

                    _cursor.executemany(
                        sql=helper_words_insert_query,
                        param_list=_params,
                    )

        await sync_to_async(_sync_version)(category)

    @override
    async def _get_by_uuid(self, category_uuid: UUID) -> Category | None:
        def _sync_version(_category_uuid: UUID) -> Category | None:
            _category_select_query = """
                SELECT c.category_uuid, c.name, ch.word
                FROM categories c
                INNER JOIN category_helper_words ch
                ON c.category_uuid = ch.category_uuid
                WHERE c.category_uuid = %s;
            """
            _cursor: CursorWrapper

            with connection.cursor() as _cursor:
                _cursor.execute(sql=_category_select_query, params=[_category_uuid])
                _rows: list[tuple[UUID, str, str | None]] = _cursor.fetchall()

                if _rows:
                    _first_row = _rows[0]
                    _category_uuid = _first_row[0]
                    _category_name = _first_row[1]
                    _helper_words: list[str] = []
                    for row in _rows:
                        _word = row[2]
                        if _word is not None:
                            _helper_words.append(_word)
                    return Category(
                        category_uuid=_category_uuid,
                        name=_category_name,
                        helper_words=CategoryHelperWords(words=frozenset(_helper_words)),
                    )
                return None

        return await sync_to_async(_sync_version)(category_uuid)

    @override
    async def _get_by_name(self, category_name: str) -> Category | None:
        def _sync_version(category_name_: str) -> Category | None:
            _category_select_query = """
                SELECT c.category_uuid, c.name, ch.word
                FROM categories c
                INNER JOIN category_helper_words ch
                ON c.category_uuid = ch.category_uuid
                WHERE c.name = %s;
            """
            _cursor: CursorWrapper
            with connection.cursor() as _cursor:
                _cursor.execute(sql=_category_select_query, params=[category_name_])
                _rows: list[tuple[UUID, str, str | None]] = _cursor.fetchall()
                if _rows:
                    _first_row = _rows[0]
                    _category_uuid = _first_row[0]
                    _category_name = _first_row[1]
                    _helper_words: list[str] = []
                    for _row in _rows:
                        _word = _row[2]
                        if _word is not None:
                            _helper_words.append(_word)
                    return Category(
                        category_uuid=_category_uuid,
                        name=_category_name,
                        helper_words=CategoryHelperWords(words=frozenset(_helper_words)),
                    )
                return None

        return await sync_to_async(_sync_version)(category_name)

    @override
    async def _update(self, updated_category: Category) -> None:
        def _sync_version(_updated_category: Category) -> None:
            _category_uuid = _updated_category.get_uuid()
            _entity_helper_words = _updated_category.get_helper_words()

            _category_update_query = """
                UPDATE categories
                SET name = %s,
                    updated_at = Now()
                WHERE category_uuid = %s
            """
            _select_words_query = """
                SELECT word FROM category_helper_words
                WHERE category_uuid = %s
            """
            _delete_words_query = """
                DELETE FROM category_helper_words
                WHERE category_uuid = %s AND word = ANY(%s)
            """
            _insert_word_query = """
                INSERT INTO category_helper_words (category_uuid, word)
                VALUES (%s, %s);
            """
            _cursor: CursorWrapper
            with connection.cursor() as _cursor:
                _cursor.execute(sql=_category_update_query, params=[_updated_category.get_name(), _category_uuid])
                _cursor.execute(sql=_select_words_query, params=[_category_uuid])
                _rows = _cursor.fetchall()
                _current_helper_words_in_db = frozenset(str(row[0]) for row in _rows)

                _helper_words_to_remove = _current_helper_words_in_db - _entity_helper_words
                if _helper_words_to_remove:
                    _cursor.execute(
                        sql=_delete_words_query,
                        params=[_category_uuid, list(_helper_words_to_remove)],
                    )

                _helper_words_to_add = _entity_helper_words - _current_helper_words_in_db
                if _helper_words_to_add:
                    _insert_params = [(_category_uuid, word) for word in _helper_words_to_add]
                    _cursor.executemany(
                        sql=_insert_word_query,
                        param_list=_insert_params,
                    )

        return await sync_to_async(_sync_version)(updated_category)

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
