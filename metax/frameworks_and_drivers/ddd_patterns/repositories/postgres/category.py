from typing import override
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


class DjangoPostgresqlCategoryRepository(CategoryRepository):
    @override
    async def all(self) -> list[Category]:
        def _sync_version() -> list[Category]:
            with connection.cursor() as cursor:
                cursor.execute("SELECT uuid, name, name_hy, name_ru, created_at, updated_at FROM categories")
                rows = cursor.fetchall()
            return [
                Category(uuid_=r[0], name=r[1], name_hy=r[2], name_ru=r[3], created_at=r[4], updated_at=r[5])
                for r in rows
            ]

        return await sync_to_async(_sync_version)()

    @override
    async def list_paginated_and_total_count(self, limit: int, offset: int) -> tuple[TotalCount, list[Category]]:
        def _sync_version(_limit: int, _offset: int) -> tuple[TotalCount, list[Category]]:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*)::bigint FROM categories")
                total_count: int = cursor.fetchone()[0]
                cursor.execute(
                    """
                    SELECT uuid, name, name_hy, name_ru, created_at, updated_at
                    FROM categories
                    ORDER BY name ASC
                    LIMIT %s OFFSET %s
                    """,
                    [_limit, _offset],
                )
                rows = cursor.fetchall()
            categories = [
                Category(uuid_=r[0], name=r[1], name_hy=r[2], name_ru=r[3], created_at=r[4], updated_at=r[5])
                for r in rows
            ]
            return total_count, categories

        return await sync_to_async(_sync_version)(limit, offset)

    @override
    async def _add(self, category: Category) -> None:
        def _sync_version(_category: Category) -> None:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO categories (uuid, name, name_hy, name_ru, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    [
                        _category.get_uuid(), _category.get_name(),
                        _category.get_name_hy(), _category.get_name_ru(),
                        _category.get_created_at(), _category.get_updated_at(),
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
                cursor.execute(
                    "SELECT uuid, name, name_hy, name_ru, created_at, updated_at FROM categories WHERE name = %s",
                    [_name],
                )
                row = cursor.fetchone()
            if row is None:
                return None
            return Category(
                uuid_=row[0],
                name=row[1],
                name_hy=row[2],
                name_ru=row[3],
                created_at=row[4],
                updated_at=row[5],
            )

        return await sync_to_async(_sync_version)(name)

    @override
    async def _get_by_uuid(self, uuid_: UUID) -> Category | None:
        def _sync_version(_uuid: UUID) -> Category | None:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT uuid, name, name_hy, name_ru, created_at, updated_at FROM categories WHERE uuid = %s",
                    [_uuid],
                )
                row = cursor.fetchone()
            if row is None:
                return None
            return Category(
                uuid_=row[0],
                name=row[1],
                name_hy=row[2],
                name_ru=row[3],
                created_at=row[4],
                updated_at=row[5],
            )

        return await sync_to_async(_sync_version)(uuid_)

    @override
    async def _update(self, updated_category: Category) -> None:
        def _sync_version(_cat: Category) -> None:
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
