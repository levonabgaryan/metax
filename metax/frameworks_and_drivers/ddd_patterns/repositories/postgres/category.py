from datetime import datetime
from typing import override
from uuid import UUID

from asgiref.sync import sync_to_async
from django.db import connection
from django.db.backends.utils import CursorWrapper

from metax.core.application.ports.ddd_patterns.repository.entites_repositories.category import (
    CategoryRepository,
)
from metax.core.domain.entities.category.entity import (
    Category,
)

type CategoryName = str
type HelperWord = str


class DjangoPostgresqlCategoryRepository(CategoryRepository):
    @override
    async def _add(self, category: Category) -> None:
        def _sync_version(_category: Category) -> None:
            category_insert_query = """
                INSERT INTO categories (category_uuid, name, created_at, updated_at)
                VALUES (%s, %s, %s, %s);
            """
            cursor: CursorWrapper
            with connection.cursor() as cursor:
                cursor.execute(
                    sql=category_insert_query,
                    params=[
                        _category.get_uuid(),
                        _category.get_name(),
                        _category.get_created_at(),
                        _category.get_updated_at(),
                    ],
                )

                if _category.get_helper_words():
                    helper_words_insert_query = """
                        INSERT INTO category_helper_words (category_uuid, word, created_at, updated_at)
                        VALUES (%s, %s, %s, %s);
                    """
                    params = [
                        (
                            _category.get_uuid(),
                            word,
                            _category.get_created_at(),
                            _category.get_updated_at(),
                        )
                        for word in _category.get_helper_words()
                    ]

                    cursor.executemany(
                        sql=helper_words_insert_query,
                        param_list=params,
                    )

        await sync_to_async(_sync_version)(category)

    @override
    async def _get_by_uuid(self, uuid_: UUID) -> Category | None:
        def _sync_version(_category_uuid: UUID) -> Category | None:
            category_select_query = """
                SELECT
                    c.category_uuid,
                    c.name,
                    c.created_at,
                    c.updated_at,
                    ch.word
                FROM categories c
                INNER JOIN category_helper_words ch
                ON c.category_uuid = ch.category_uuid
                WHERE c.category_uuid = %s;
            """
            cursor: CursorWrapper

            with connection.cursor() as cursor:
                cursor.execute(sql=category_select_query, params=[_category_uuid])
                rows: list[tuple[UUID, str, datetime, datetime, str | None]] = cursor.fetchall()

                if rows:
                    first_row = rows[0]
                    db_category_uuid = first_row[0]
                    category_name = first_row[1]
                    created_at = first_row[2]
                    updated_at = first_row[3]
                    helper_words: frozenset[str] = frozenset(row[4] for row in rows if row[4] is not None)

                    return Category(
                        uuid_=db_category_uuid,
                        name=category_name,
                        helper_words=frozenset(helper_words),
                        created_at=created_at,
                        updated_at=updated_at,
                    )
                return None

        return await sync_to_async(_sync_version)(uuid_)

    @override
    async def _get_by_name(self, name: str) -> Category | None:
        def _sync_version(category_name_: str) -> Category | None:
            category_select_query = """
                SELECT
                    c.category_uuid,
                    c.name,
                    c.created_at,
                    c.updated_at,
                    ch.word
                FROM categories c
                INNER JOIN category_helper_words ch
                ON c.category_uuid = ch.category_uuid
                WHERE c.name = %s;
            """
            cursor: CursorWrapper
            with connection.cursor() as cursor:
                cursor.execute(sql=category_select_query, params=[category_name_])
                rows: list[tuple[UUID, str, datetime, datetime, str | None]] = cursor.fetchall()
                if rows:
                    first_row = rows[0]
                    category_uuid = first_row[0]
                    category_name = first_row[1]
                    created_at = first_row[2]
                    updated_at = first_row[3]
                    helper_words: frozenset[str] = frozenset(row[4] for row in rows if row[4] is not None)
                    return Category(
                        uuid_=category_uuid,
                        name=category_name,
                        helper_words=frozenset(helper_words),
                        created_at=created_at,
                        updated_at=updated_at,
                    )
                return None

        return await sync_to_async(_sync_version)(name)

    @override
    async def _update(self, updated_category: Category) -> None:
        def _sync_version(_updated_category: Category) -> None:
            category_uuid = _updated_category.get_uuid()
            entity_helper_words = _updated_category.get_helper_words()

            category_update_query = """
                UPDATE categories
                SET name = %s,
                    updated_at = %s
                WHERE category_uuid = %s
            """
            select_words_query = """
                SELECT word FROM category_helper_words
                WHERE category_uuid = %s
            """
            delete_words_query = """
                DELETE FROM category_helper_words
                WHERE category_uuid = %s AND word = ANY(%s)
            """
            insert_word_query = """
                INSERT INTO category_helper_words (category_uuid, word, created_at, updated_at)
                VALUES (%s, %s, %s, %s);
            """
            cursor: CursorWrapper
            with connection.cursor() as cursor:
                cursor.execute(
                    sql=category_update_query,
                    params=[_updated_category.get_name(), _updated_category.get_updated_at(), category_uuid],
                )
                cursor.execute(sql=select_words_query, params=[category_uuid])
                rows = cursor.fetchall()
                current_helper_words_in_db = frozenset(row[0] for row in rows if row[0] is not None)

                helper_words_to_remove = current_helper_words_in_db - entity_helper_words
                if helper_words_to_remove:
                    cursor.execute(
                        sql=delete_words_query,
                        params=[category_uuid, list(helper_words_to_remove)],
                    )

                helper_words_to_add = entity_helper_words - current_helper_words_in_db
                if helper_words_to_add:
                    insert_params = [
                        (
                            category_uuid,
                            word,
                            _updated_category.get_updated_at(),
                            _updated_category.get_updated_at(),
                        )
                        for word in helper_words_to_add
                    ]
                    cursor.executemany(
                        sql=insert_word_query,
                        param_list=insert_params,
                    )

        return await sync_to_async(_sync_version)(updated_category)

    @override
    async def get_all(self) -> list[Category]:
        def _sync_version() -> list[Category]:
            select_all_query = """
                SELECT
                    c.category_uuid,
                    c.name,
                    c.created_at,
                    c.updated_at,
                    ch.word
                FROM categories c
                LEFT JOIN category_helper_words ch
                ON c.category_uuid = ch.category_uuid
            """
            cursor: CursorWrapper
            with connection.cursor() as cursor:
                cursor.execute(sql=select_all_query)
                rows: list[tuple[UUID, str, datetime, datetime, str | None]] = cursor.fetchall()

            category_map: dict[UUID, tuple[CategoryName, datetime, datetime, list[HelperWord]]] = {}
            for row in rows:
                category_uuid: UUID = row[0]
                category_name: CategoryName = row[1]
                created_at: datetime = row[2]
                updated_at: datetime = row[3]
                category_helper_word: HelperWord | None = row[4]
                if category_uuid not in category_map:
                    category_map[category_uuid] = (category_name, created_at, updated_at, [])
                if category_helper_word is not None:
                    category_map[category_uuid][3].append(category_helper_word)

            return [
                Category(
                    uuid_=category_uid,
                    name=name_and_words[0],
                    helper_words=frozenset(name_and_words[3]),
                    created_at=name_and_words[1],
                    updated_at=name_and_words[2],
                )
                for category_uid, name_and_words in category_map.items()
            ]

        return await sync_to_async(_sync_version)()
