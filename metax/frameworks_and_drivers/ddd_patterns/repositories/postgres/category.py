from datetime import datetime
from typing import override
from uuid import UUID

from asgiref.sync import sync_to_async
from django.db import connection
from django.db.backends.utils import CursorWrapper

from metax.core.application.ports.ddd_patterns.repository.entites_repositories.category import (
    CategoryRepository,
)
from metax.core.domain.ddd_patterns.general_value_objects import EntityDateTimeDetails, UUIDValueObject
from metax.core.domain.entities.category.entity import (
    Category,
)
from metax.core.domain.entities.category.value_objects import CategoryHelperWords

type CategoryName = str
type HelperWord = str


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

                if _category.get_helper_words():
                    helper_words_insert_query = """
                        INSERT INTO category_helper_words (category_uuid, word)
                        VALUES (%s, %s);
                    """
                    _params = [(_category.get_uuid(), word) for word in _category.get_helper_words()]

                    _cursor.executemany(
                        sql=helper_words_insert_query,
                        param_list=_params,
                    )

        await sync_to_async(_sync_version)(category)

    @override
    async def _get_by_uuid(self, category_uuid: UUID) -> Category | None:
        def _sync_version(_category_uuid: UUID) -> Category | None:
            _category_select_query = """
                SELECT c.category_uuid, c.name, c.created_at, c.updated_at, ch.word
                FROM categories c
                INNER JOIN category_helper_words ch
                ON c.category_uuid = ch.category_uuid
                WHERE c.category_uuid = %s;
            """
            _cursor: CursorWrapper

            with connection.cursor() as _cursor:
                _cursor.execute(sql=_category_select_query, params=[_category_uuid])
                _rows: list[tuple[UUID, str, datetime, datetime, str | None]] = _cursor.fetchall()

                if _rows:
                    _first_row = _rows[0]
                    _category_uuid = _first_row[0]
                    _category_name = _first_row[1]
                    _created_at = _first_row[2]
                    _updated_at = _first_row[3]
                    _helper_words: frozenset[str] = frozenset(_row[4] for _row in _rows if _row[4] is not None)

                    return Category(
                        category_uuid=UUIDValueObject.create(_category_uuid),
                        name=_category_name,
                        helper_words=CategoryHelperWords.create(words=frozenset(_helper_words)),
                        datetime_details=EntityDateTimeDetails.create(
                            created_at=_created_at, updated_at=_updated_at
                        ),
                    )
                return None

        return await sync_to_async(_sync_version)(category_uuid)

    @override
    async def _get_by_name(self, category_name: str) -> Category | None:
        def _sync_version(category_name_: str) -> Category | None:
            _category_select_query = """
                SELECT c.category_uuid, c.name, c.created_at, c.updated_at, ch.word
                FROM categories c
                INNER JOIN category_helper_words ch
                ON c.category_uuid = ch.category_uuid
                WHERE c.name = %s;
            """
            _cursor: CursorWrapper
            with connection.cursor() as _cursor:
                _cursor.execute(sql=_category_select_query, params=[category_name_])
                _rows: list[tuple[UUID, str, datetime, datetime, str | None]] = _cursor.fetchall()
                if _rows:
                    _first_row = _rows[0]
                    _category_uuid = _first_row[0]
                    _category_name = _first_row[1]
                    _created_at = _first_row[2]
                    _updated_at = _first_row[3]
                    _helper_words: frozenset[str] = frozenset(_row[4] for _row in _rows if _row[4] is not None)
                    return Category(
                        category_uuid=UUIDValueObject.create(_category_uuid),
                        name=_category_name,
                        helper_words=CategoryHelperWords.create(words=frozenset(_helper_words)),
                        datetime_details=EntityDateTimeDetails.create(
                            created_at=_created_at, updated_at=_updated_at
                        ),
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
                    updated_at = %s
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
                _cursor.execute(
                    sql=_category_update_query,
                    params=[_updated_category.get_name(), _updated_category.get_updated_at(), _category_uuid],
                )
                _cursor.execute(sql=_select_words_query, params=[_category_uuid])
                _rows = _cursor.fetchall()
                _current_helper_words_in_db = frozenset(row[0] for row in _rows if row[0] is not None)

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

    @override
    async def get_all(self) -> list[Category]:
        def _sync_version() -> list[Category]:
            select_all_query = """
                SELECT c.category_uuid, c.name, c.created_at, c.updated_at, ch.word
                FROM categories c
                LEFT JOIN category_helper_words ch
                ON c.category_uuid = ch.category_uuid
            """
            _cursor: CursorWrapper
            with connection.cursor() as _cursor:
                _cursor.execute(sql=select_all_query)
                _rows: list[tuple[UUID, str, datetime, datetime, str | None]] = _cursor.fetchall()

            _category_map: dict[UUID, tuple[CategoryName, datetime, datetime, list[HelperWord]]] = {}
            for _row in _rows:
                _category_uuid: UUID = _row[0]
                _category_name: CategoryName = _row[1]
                _created_at: datetime = _row[2]
                _updated_at: datetime = _row[3]
                _category_helper_word: HelperWord | None = _row[4]
                if _category_uuid not in _category_map:
                    _category_map[_category_uuid] = (_category_name, _created_at, _updated_at, [])
                if _category_helper_word is not None:
                    _category_map[_category_uuid][3].append(_category_helper_word)

            return [
                Category(
                    category_uuid=UUIDValueObject.create(_category_uid),
                    name=_name_and_words[0],
                    helper_words=CategoryHelperWords.create(words=frozenset(_name_and_words[3])),
                    datetime_details=EntityDateTimeDetails.create(
                        created_at=_name_and_words[1], updated_at=_name_and_words[2]
                    ),
                )
                for _category_uid, _name_and_words in _category_map.items()
            ]

        return await sync_to_async(_sync_version)()
