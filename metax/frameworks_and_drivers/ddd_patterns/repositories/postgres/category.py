from datetime import datetime
from typing import override
from uuid import UUID

from asgiref.sync import sync_to_async
from django.db import connection
from django.db.backends.utils import CursorWrapper

from metax.core.application.ports.ddd_patterns.repository.entites_repositories.category import (
    CategoryRepository,
)
from metax.core.domain.entities.category.aggregate_root_entity import Category
from metax.core.domain.entities.category_helper_word.entity import CategoryHelperWord

type CategoryName = str


class DjangoPostgresqlCategoryRepository(CategoryRepository):
    @override
    async def get_all(self) -> list[Category]:
        def _sync_version() -> list[Category]:
            select_all_query = """
                SELECT
                    c.category_uuid,
                    c.name,
                    c.created_at,
                    c.updated_at,
                    ch.helper_word_uuid,
                    ch.helper_word_text,
                    ch.created_at,
                    ch.updated_at
                FROM categories c
                LEFT JOIN category_helper_words ch
                ON c.category_uuid = ch.category_uuid
            """
            cursor: CursorWrapper
            with connection.cursor() as cursor:
                cursor.execute(sql=select_all_query)
                rows: list[
                    tuple[
                        UUID,
                        CategoryName,
                        datetime,
                        datetime,
                        UUID | None,
                        str | None,
                        datetime | None,
                        datetime | None,
                    ]
                ] = cursor.fetchall()

            category_map: dict[
                UUID,
                tuple[CategoryName, datetime, datetime, list[CategoryHelperWord]],
            ] = {}
            for row in rows:
                category_uuid = row[0]
                category_name = row[1]
                category_created_at = row[2]
                category_updated_at = row[3]
                helper_word_uuid = row[4]
                if category_uuid not in category_map:
                    category_map[category_uuid] = (
                        category_name,
                        category_created_at,
                        category_updated_at,
                        [],
                    )

                helper_word_text = row[5]
                helper_word_created_at = row[6]
                helper_word_updated_at = row[7]
                if (
                    helper_word_uuid is None
                    or helper_word_text is None
                    or helper_word_created_at is None
                    or helper_word_updated_at is None
                ):
                    continue

                category_map[category_uuid][3].append(
                    CategoryHelperWord(
                        uuid_=helper_word_uuid,
                        text=helper_word_text,
                        created_at=helper_word_created_at,
                        updated_at=helper_word_updated_at,
                    ),
                )

            return [
                Category(
                    uuid_=category_uuid,
                    name=category_name,
                    helper_words=helper_words,
                    created_at=category_created_at,
                    updated_at=category_updated_at,
                )
                for (
                    category_uuid,
                    (category_name, category_created_at, category_updated_at, helper_words),
                ) in category_map.items()
            ]

        return await sync_to_async(_sync_version)()

    @override
    async def _update(self, updated_category: Category) -> None:
        def _sync_version(_updated_category: Category) -> None:
            category_uuid = _updated_category.get_uuid()
            entity_helper_words = _updated_category.get_helper_words()

            category_update_query = """
                UPDATE categories
                SET name = %s, updated_at = %s
                WHERE category_uuid = %s
            """
            helper_words_select_query = """
                SELECT helper_word_uuid, helper_word_text, created_at, updated_at
                FROM category_helper_words
                WHERE category_uuid = %s
            """
            helper_words_delete_query = """
                DELETE FROM category_helper_words
                WHERE helper_word_uuid = %s
            """
            helper_words_insert_query = """
                INSERT INTO category_helper_words
                    (helper_word_uuid, helper_word_text, category_uuid, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            helper_words_update_query = """
                UPDATE category_helper_words
                SET helper_word_text = %s, updated_at = %s
                WHERE helper_word_uuid = %s
            """

            cursor: CursorWrapper
            with connection.cursor() as cursor:
                cursor.execute(
                    sql=category_update_query,
                    params=[
                        _updated_category.get_name(),
                        _updated_category.get_updated_at(),
                        category_uuid,
                    ],
                )
                cursor.execute(sql=helper_words_select_query, params=[category_uuid])
                rows: list[tuple[UUID, str, datetime, datetime]] = cursor.fetchall()
                db_helper_words = tuple(
                    CategoryHelperWord(
                        uuid_=row[0],
                        text=row[1],
                        created_at=row[2],
                        updated_at=row[3],
                    )
                    for row in rows
                )

                db_map = {helper_word.get_uuid(): helper_word for helper_word in db_helper_words}
                entity_map = {helper_word.get_uuid(): helper_word for helper_word in entity_helper_words}
                db_ids = set(db_map.keys())
                entity_ids = set(entity_map.keys())

                to_delete_ids = db_ids - entity_ids
                to_insert_ids = entity_ids - db_ids
                general_ids = db_ids & entity_ids
                to_update_ids = [
                    helper_word_uuid
                    for helper_word_uuid in general_ids
                    if (
                        db_map[helper_word_uuid].get_text() != entity_map[helper_word_uuid].get_text()
                        or db_map[helper_word_uuid].get_updated_at()
                        != entity_map[helper_word_uuid].get_updated_at()
                    )
                ]

                if to_delete_ids:
                    cursor.executemany(
                        sql=helper_words_delete_query,
                        param_list=[(helper_word_uuid,) for helper_word_uuid in to_delete_ids],
                    )
                if to_insert_ids:
                    cursor.executemany(
                        sql=helper_words_insert_query,
                        param_list=[
                            (
                                entity_map[helper_word_uuid].get_uuid(),
                                entity_map[helper_word_uuid].get_text(),
                                category_uuid,
                                entity_map[helper_word_uuid].get_created_at(),
                                entity_map[helper_word_uuid].get_updated_at(),
                            )
                            for helper_word_uuid in to_insert_ids
                        ],
                    )
                if to_update_ids:
                    cursor.executemany(
                        sql=helper_words_update_query,
                        param_list=[
                            (
                                entity_map[helper_word_uuid].get_text(),
                                entity_map[helper_word_uuid].get_updated_at(),
                                helper_word_uuid,
                            )
                            for helper_word_uuid in to_update_ids
                        ],
                    )

        await sync_to_async(_sync_version)(updated_category)

    @override
    async def _add(self, category: Category) -> None:
        def _sync_version(_category: Category) -> None:
            category_insert_query = """
                INSERT INTO categories (category_uuid, name, created_at, updated_at)
                VALUES (%s, %s, %s, %s)
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
                        INSERT INTO category_helper_words
                            (helper_word_uuid, helper_word_text, category_uuid, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.executemany(
                        sql=helper_words_insert_query,
                        param_list=[
                            (
                                helper_word.get_uuid(),
                                helper_word.get_text(),
                                _category.get_uuid(),
                                helper_word.get_created_at(),
                                helper_word.get_updated_at(),
                            )
                            for helper_word in _category.get_helper_words()
                        ],
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
                    ch.helper_word_uuid,
                    ch.helper_word_text,
                    ch.created_at,
                    ch.updated_at
                FROM categories c
                LEFT JOIN category_helper_words ch
                ON c.category_uuid = ch.category_uuid
                WHERE c.category_uuid = %s
            """
            cursor: CursorWrapper
            with connection.cursor() as cursor:
                cursor.execute(sql=category_select_query, params=[_category_uuid])
                rows: list[
                    tuple[
                        UUID,
                        CategoryName,
                        datetime,
                        datetime,
                        UUID | None,
                        str | None,
                        datetime | None,
                        datetime | None,
                    ]
                ] = cursor.fetchall()

            if not rows:
                return None

            first_row = rows[0]
            helper_words = [
                CategoryHelperWord(
                    uuid_=row[4],
                    text=row[5],
                    created_at=row[6],
                    updated_at=row[7],
                )
                for row in rows
                if row[4] is not None and row[5] is not None and row[6] is not None and row[7] is not None
            ]
            return Category(
                uuid_=first_row[0],
                name=first_row[1],
                helper_words=helper_words,
                created_at=first_row[2],
                updated_at=first_row[3],
            )

        return await sync_to_async(_sync_version)(uuid_)

    @override
    async def _get_by_name(self, name: str) -> Category | None:
        def _sync_version(category_name: str) -> Category | None:
            category_select_query = """
                SELECT
                    c.category_uuid,
                    c.name,
                    c.created_at,
                    c.updated_at,
                    ch.helper_word_uuid,
                    ch.helper_word_text,
                    ch.created_at,
                    ch.updated_at
                FROM categories c
                LEFT JOIN category_helper_words ch
                ON c.category_uuid = ch.category_uuid
                WHERE c.name = %s
            """
            cursor: CursorWrapper
            with connection.cursor() as cursor:
                cursor.execute(sql=category_select_query, params=[category_name])
                rows: list[
                    tuple[
                        UUID,
                        CategoryName,
                        datetime,
                        datetime,
                        UUID | None,
                        str | None,
                        datetime | None,
                        datetime | None,
                    ]
                ] = cursor.fetchall()

            if not rows:
                return None

            first_row = rows[0]
            helper_words = [
                CategoryHelperWord(
                    uuid_=row[4],
                    text=row[5],
                    created_at=row[6],
                    updated_at=row[7],
                )
                for row in rows
                if row[4] is not None and row[5] is not None and row[6] is not None and row[7] is not None
            ]
            return Category(
                uuid_=first_row[0],
                name=first_row[1],
                helper_words=helper_words,
                created_at=first_row[2],
                updated_at=first_row[3],
            )

        return await sync_to_async(_sync_version)(name)
