from collections.abc import AsyncIterator, Iterator
from typing import override
from uuid import UUID

from asgiref.sync import sync_to_async
from django.db import IntegrityError, connection
from django.db.backends.utils import CursorWrapper

from metax.core.application.ports.ddd_patterns.repository.entites_repositories.retailer import (
    RetailerRepository,
)
from metax.core.application.ports.ddd_patterns.repository.errors import EntityAlreadyExistsError
from metax.core.domain.entities.retailer.aggregate_root_entity import Retailer
from metax.frameworks_and_drivers.ddd_patterns.repositories.postgres.utils import (
    extract_field_from_integrity_message,
)


class DjangoPostgresqlRetailerRepository(RetailerRepository):
    @override
    async def all(self) -> AsyncIterator[Retailer]:
        def _sync_version() -> Iterator[Retailer]:
            select_all_query = """
                SELECT
                    retailer_uuid,
                    name,
                    home_page_url,
                    phone_number,
                    created_at,
                    updated_at
                FROM retailers
                ORDER BY name ASC
            """
            cursor: CursorWrapper
            with connection.cursor() as cursor:
                cursor.execute(sql=select_all_query)
                rows = cursor.fetchall()
            return (
                Retailer(
                    uuid_=row[0],
                    name=row[1],
                    home_page_url=row[2],
                    phone_number=row[3],
                    created_at=row[4],
                    updated_at=row[5],
                )
                for row in rows
            )

        retailers = await sync_to_async(_sync_version)()
        for retailer in retailers:
            yield retailer

    @override
    async def list_paginated_and_total_count(self, limit: int, offset: int) -> tuple[int, list[Retailer]]:
        def _sync_version(_limit: int, _offset: int) -> tuple[int, list[Retailer]]:
            count_query = """
                SELECT COUNT(*)::bigint
                FROM categories c;
            """

            query_ = """
                SELECT
                    retailer_uuid,
                    name,
                    home_page_url,
                    phone_number,
                    created_at,
                    updated_at
                FROM retailers
                ORDER BY name ASC
                LIMIT %s OFFSET %s;
            """
            cursor: CursorWrapper
            with connection.cursor() as cursor:
                cursor.execute(count_query)
                total_count: int = cursor.fetchone()[0]

                cursor.execute(
                    sql=query_,
                    params=[_limit, _offset],
                )
                rows = cursor.fetchall()
                retailers = [
                    Retailer(
                        uuid_=row[0],
                        name=row[1],
                        home_page_url=row[2],
                        phone_number=row[3],
                        created_at=row[4],
                        updated_at=row[5],
                    )
                    for row in rows
                ]
            return total_count, retailers

        return await sync_to_async(_sync_version)(limit, offset)

    @override
    async def _add(self, retailer: Retailer) -> None:
        def _sync_version(_retailer: Retailer) -> None:
            insert_query = """
                INSERT INTO retailers (retailer_uuid, name, home_page_url, phone_number, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor: CursorWrapper
            with connection.cursor() as cursor:
                cursor.execute(
                    sql=insert_query,
                    params=[
                        _retailer.get_uuid(),
                        _retailer.get_name(),
                        _retailer.get_home_page_url(),
                        _retailer.get_phone_number(),
                        _retailer.get_created_at(),
                        _retailer.get_updated_at(),
                    ],
                )

        try:
            await sync_to_async(_sync_version)(retailer)
        except IntegrityError as err:
            field_name, field_value = extract_field_from_integrity_message(str(err))
            raise EntityAlreadyExistsError(
                entity_type="retailer",
                entity_field_name=field_name,
                entity_field_value=field_value,
            ) from err

    @override
    async def _delete_by_uuid_and_return_uuid(self, uuid_: UUID) -> UUID | None:
        def _sync_version(_retailer_uuid: UUID) -> UUID | None:
            delete_query = """
                DELETE FROM retailers
                WHERE retailer_uuid = %s;
            """
            cursor: CursorWrapper
            with connection.cursor() as cursor:
                cursor.execute(sql=delete_query, params=[_retailer_uuid])
                if cursor.rowcount == 0:
                    return None
                return _retailer_uuid

        return await sync_to_async(_sync_version)(uuid_)

    @override
    async def _get_by_name(self, name: str) -> Retailer | None:
        def _sync_version(_retailer_name: str) -> Retailer | None:
            select_query = """
                SELECT
                    retailer_uuid,
                    name,
                    home_page_url,
                    phone_number,
                    created_at,
                    updated_at
                FROM retailers
                WHERE name = %s
            """
            cursor: CursorWrapper
            with connection.cursor() as cursor:
                cursor.execute(sql=select_query, params=[_retailer_name])
                row = cursor.fetchone()
                if row is None:
                    return None
                return Retailer(
                    uuid_=row[0],
                    name=row[1],
                    home_page_url=row[2],
                    phone_number=row[3],
                    created_at=row[4],
                    updated_at=row[5],
                )

        return await sync_to_async(_sync_version)(name)

    @override
    async def _get_by_uuid(self, uuid_: UUID) -> Retailer | None:
        def _sync_version(_retailer_uuid: UUID) -> Retailer | None:
            select_query = """
                SELECT
                    retailer_uuid,
                    name,
                    home_page_url,
                    phone_number,
                    created_at,
                    updated_at
                FROM retailers
                WHERE retailer_uuid = %s
            """
            cursor: CursorWrapper
            with connection.cursor() as cursor:
                cursor.execute(sql=select_query, params=[_retailer_uuid])
                row = cursor.fetchone()
                if row is None:
                    return None
                return Retailer(
                    uuid_=row[0],
                    name=row[1],
                    home_page_url=row[2],
                    phone_number=row[3],
                    created_at=row[4],
                    updated_at=row[5],
                )

        return await sync_to_async(_sync_version)(uuid_)

    @override
    async def _update(self, updated_retailer: Retailer) -> None:
        def _sync_version(_updated_retailer: Retailer) -> None:
            update_query = """
                UPDATE retailers
                SET name = %s, home_page_url = %s, phone_number = %s, updated_at = %s
                WHERE retailer_uuid = %s
            """
            cursor: CursorWrapper
            with connection.cursor() as cursor:
                cursor.execute(
                    sql=update_query,
                    params=[
                        _updated_retailer.get_name(),
                        _updated_retailer.get_home_page_url(),
                        _updated_retailer.get_phone_number(),
                        _updated_retailer.get_updated_at(),
                        _updated_retailer.get_uuid(),
                    ],
                )

        try:
            return await sync_to_async(_sync_version)(updated_retailer)
        except IntegrityError as err:
            field_name, field_value = extract_field_from_integrity_message(str(err))
            raise EntityAlreadyExistsError(
                entity_type="retailer",
                entity_field_name=field_name,
                entity_field_value=field_value,
            ) from err
