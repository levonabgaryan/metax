import re
from typing import Any, override
from uuid import UUID

from asgiref.sync import sync_to_async
from django.db import IntegrityError, connection

from metax.core.application.ports.ddd_patterns.repository.entites_repositories.category import (
    CategoryRepository,
    TotalCount,
)
from metax.core.application.ports.ddd_patterns.repository.errors import EntityAlreadyExistsError
from metax.core.domain.entities.category.aggregate_root_entity import Category
from metax.frameworks_and_drivers.ddd_patterns.repositories.postgres.utils import (
    extract_field_from_integrity_message,
)


def _parse_phrases(raw: str | None) -> list[str]:
    """Split stored ``examples`` / ``keywords`` text (newline- or comma-separated) into a clean list.

    Returns:
        Trimmed, non-empty phrases in their stored order.
    """
    if not raw:
        return []
    return [part.strip() for part in re.split(r"[,\n]", raw) if part.strip()]


def _serialize_phrases(phrases: list[str]) -> str:
    """Render a phrase list back to the stored newline-separated text.

    Returns:
        The phrases joined by newlines (empty string for none).
    """
    return "\n".join(phrases)


# Every category read selects these columns, in the order ``_row_to_category`` expects.
_SELECT_CATEGORIES = """
    SELECT uuid, name, name_hy, name_ru, created_at, updated_at, examples, keywords
    FROM categories
"""
_SELECT_CATEGORIES_PAGE = """
    SELECT uuid, name, name_hy, name_ru, created_at, updated_at, examples, keywords
    FROM categories
    ORDER BY name ASC
    LIMIT %s OFFSET %s
"""
_SELECT_CATEGORY_BY_NAME = """
    SELECT uuid, name, name_hy, name_ru, created_at, updated_at, examples, keywords
    FROM categories
    WHERE name = %s
"""
_SELECT_CATEGORY_BY_UUID = """
    SELECT uuid, name, name_hy, name_ru, created_at, updated_at, examples, keywords
    FROM categories
    WHERE uuid = %s
"""


def _row_to_category(row: tuple[Any, ...]) -> Category:
    return Category(
        uuid_=row[0],
        name=row[1],
        name_hy=row[2],
        name_ru=row[3],
        created_at=row[4],
        updated_at=row[5],
        examples=_parse_phrases(row[6]),
        keywords=_parse_phrases(row[7]),
    )


class DjangoPostgresqlCategoryRepository(CategoryRepository):
    @override
    async def all(self) -> list[Category]:
        def _sync_version() -> list[Category]:
            with connection.cursor() as cursor:
                cursor.execute(_SELECT_CATEGORIES)
                rows = cursor.fetchall()
            return [_row_to_category(row) for row in rows]

        return await sync_to_async(_sync_version)()

    @override
    async def list_paginated_and_total_count(self, limit: int, offset: int) -> tuple[TotalCount, list[Category]]:
        def _sync_version(_limit: int, _offset: int) -> tuple[TotalCount, list[Category]]:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*)::bigint FROM categories")
                total_count: int = cursor.fetchone()[0]
                cursor.execute(_SELECT_CATEGORIES_PAGE, [_limit, _offset])
                rows = cursor.fetchall()
            return total_count, [_row_to_category(row) for row in rows]

        return await sync_to_async(_sync_version)(limit, offset)

    @override
    async def _add(self, category: Category) -> None:
        def _sync_version(_category: Category) -> None:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO categories
                        (uuid, name, name_hy, name_ru, created_at, updated_at, examples, keywords)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    [
                        _category.get_uuid(), _category.get_name(),
                        _category.get_name_hy(), _category.get_name_ru(),
                        _category.get_created_at(), _category.get_updated_at(),
                        _serialize_phrases(_category.get_examples()),
                        _serialize_phrases(_category.get_keywords()),
                    ],
                )

        try:
            await sync_to_async(_sync_version)(category)
        except IntegrityError as err:
            field_name, field_value = extract_field_from_integrity_message(str(err))
            raise EntityAlreadyExistsError(
                entity_type="category",
                entity_field_name=field_name,
                entity_field_value=field_value,
            ) from err

    @override
    async def _delete_by_uuid_and_return_uuid(self, uuid_: UUID) -> UUID | None:
        def _sync_version(_uuid: UUID) -> UUID | None:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE discounted_products SET category_uuid = NULL WHERE category_uuid = %s",
                    [_uuid],
                )
                cursor.execute("DELETE FROM categories WHERE uuid = %s", [_uuid])
                return _uuid if cursor.rowcount > 0 else None

        return await sync_to_async(_sync_version)(uuid_)

    @override
    async def _get_by_name(self, name: str) -> Category | None:
        def _sync_version(_name: str) -> Category | None:
            with connection.cursor() as cursor:
                cursor.execute(_SELECT_CATEGORY_BY_NAME, [_name])
                row = cursor.fetchone()
            return _row_to_category(row) if row is not None else None

        return await sync_to_async(_sync_version)(name)

    @override
    async def _get_by_uuid(self, uuid_: UUID) -> Category | None:
        def _sync_version(_uuid: UUID) -> Category | None:
            with connection.cursor() as cursor:
                cursor.execute(_SELECT_CATEGORY_BY_UUID, [_uuid])
                row = cursor.fetchone()
            return _row_to_category(row) if row is not None else None

        return await sync_to_async(_sync_version)(uuid_)

    @override
    async def _update(self, updated_category: Category) -> None:
        def _sync_version(_cat: Category) -> None:
            # ``examples`` and ``keywords`` are intentionally not updated here: they are curated via the
            # Django admin (or the seed migrations), so the entity-update path must not clobber them.
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE categories SET name = %s, name_hy = %s, name_ru = %s, updated_at = %s WHERE uuid = %s",
                    [
                        _cat.get_name(),
                        _cat.get_name_hy(),
                        _cat.get_name_ru(),
                        _cat.get_updated_at(),
                        _cat.get_uuid(),
                    ],
                )

        try:
            await sync_to_async(_sync_version)(updated_category)
        except IntegrityError as err:
            field_name, field_value = extract_field_from_integrity_message(str(err))
            raise EntityAlreadyExistsError(
                entity_type="category",
                entity_field_name=field_name,
                entity_field_value=field_value,
            ) from err
