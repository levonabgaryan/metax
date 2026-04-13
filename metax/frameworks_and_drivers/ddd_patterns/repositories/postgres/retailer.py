from typing import AsyncIterator, Iterator, override
from uuid import UUID

from asgiref.sync import sync_to_async
from django.db import connection
from django.db.backends.utils import CursorWrapper

from metax.core.application.ports.ddd_patterns.repository.entites_repositories.retailer import (
    RetailerRepository,
)
from metax.core.domain.entities.retailer.entity import Retailer
from metax.core.domain.entities.retailer.value_objects import RetailersNames
from metax.core.domain.general_value_objects import EntityDateTimeDetails, UUIDValueObject


class DjangoPostgresqlRetailerRepository(RetailerRepository):
    @override
    async def _add(self, retailer: Retailer) -> None:
        def _sync_version(_retailer: Retailer) -> None:
            _insert_query = """
                INSERT INTO retailers (retailer_uuid, name, url, phone_number)
                VALUES (%s, %s, %s, %s)
            """
            _cursor: CursorWrapper
            with connection.cursor() as _cursor:
                _cursor.execute(
                    sql=_insert_query,
                    params=[
                        _retailer.get_uuid(),
                        _retailer.get_name(),
                        _retailer.get_home_page_url(),
                        _retailer.get_phone_number(),
                    ],
                )

        await sync_to_async(_sync_version)(retailer)

    @override
    async def _get_by_uuid(self, retailer_uuid: UUID) -> Retailer | None:
        def _sync_version(_retailer_uuid: UUID) -> Retailer | None:
            _select_query = """
                SELECT retailer_uuid, name, url, phone_number, created_at, updated_at
                FROM retailers
                WHERE retailer_uuid = %s
            """
            _cursor: CursorWrapper
            with connection.cursor() as _cursor:
                _cursor.execute(sql=_select_query, params=[retailer_uuid])
                row = _cursor.fetchone()
                if row is None:
                    return None
                return Retailer(
                    retailer_uuid=UUIDValueObject.create(row[0]),
                    name=RetailersNames(row[1]),
                    home_page_url=row[2],
                    phone_number=row[3],
                    datetime_details=EntityDateTimeDetails.create(created_at=row[4], updated_at=row[5]),
                )

        return await sync_to_async(_sync_version)(retailer_uuid)

    @override
    async def _get_by_name(self, retailer_name: RetailersNames) -> Retailer | None:
        def _sync_version(_retailer_name: RetailersNames) -> Retailer | None:
            _select_query = """
                SELECT retailer_uuid, name, url, phone_number, created_at, updated_at
                FROM retailers
                WHERE name = %s
            """
            _cursor: CursorWrapper
            with connection.cursor() as _cursor:
                _cursor.execute(sql=_select_query, params=[_retailer_name])
                row = _cursor.fetchone()
                if row is None:
                    return None
                return Retailer(
                    retailer_uuid=UUIDValueObject.create(row[0]),
                    name=RetailersNames(row[1]),
                    home_page_url=row[2],
                    phone_number=row[3],
                    datetime_details=EntityDateTimeDetails.create(created_at=row[4], updated_at=row[5]),
                )

        return await sync_to_async(_sync_version)(retailer_name)

    @override
    async def _update(self, updated_retailer: Retailer) -> None:
        def _sync_version(_updated_retailer: Retailer) -> None:
            _update_query = """
                UPDATE retailers
                SET name = %s, url = %s, phone_number = %s
                WHERE retailer_uuid = %s
            """
            _cursor: CursorWrapper
            with connection.cursor() as _cursor:
                _cursor.execute(
                    sql=_update_query,
                    params=[
                        _updated_retailer.get_name(),
                        _updated_retailer.get_home_page_url(),
                        _updated_retailer.get_phone_number(),
                        _updated_retailer.get_uuid(),
                    ],
                )

        return await sync_to_async(_sync_version)(updated_retailer)

    @override
    async def get_all(self) -> AsyncIterator[Retailer]:
        def _sync_version() -> Iterator[Retailer]:
            _select_all_query = """
                SELECT retailer_uuid, name, url, phone_number, created_at, updated_at
                FROM retailers
                ORDER BY name ASC
            """
            _cursor: CursorWrapper
            with connection.cursor() as _cursor:
                _cursor.execute(sql=_select_all_query)
                _rows = _cursor.fetchall()
            return (
                Retailer(
                    retailer_uuid=UUIDValueObject.create(_row[0]),
                    name=RetailersNames(_row[1]),
                    home_page_url=_row[2],
                    phone_number=_row[3],
                    datetime_details=EntityDateTimeDetails.create(created_at=_row[4], updated_at=_row[5]),
                )
                for _row in _rows
            )

        _retailers = await sync_to_async(_sync_version)()
        for _retailer in _retailers:
            yield _retailer
