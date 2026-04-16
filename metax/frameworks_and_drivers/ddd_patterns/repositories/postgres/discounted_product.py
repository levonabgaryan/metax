from collections.abc import AsyncIterator
from datetime import datetime
from decimal import Decimal
from typing import override
from uuid import UUID

from asgiref.sync import sync_to_async
from django.db import connection
from django.db.backends.utils import CursorWrapper

from metax.core.application.ports.ddd_patterns.repository.entites_repositories.discounted_product import (
    DiscountedProductRepository,
    DiscountedProductWithDetails,
)
from metax.core.domain.entities.discounted_product.entity import (
    DiscountedProduct,
)

type CategoryUUID = UUID | None
type RetailerUUID = UUID
type CategoryName = str
type RetailerName = str


class DjangoPostgresqlDiscountedProductRepository(DiscountedProductRepository):
    @override
    async def add_many(self, discounted_products: list[DiscountedProduct]) -> None:
        def _sync_version(_discounted_products: list[DiscountedProduct]) -> None:
            insert_query = """
                INSERT INTO discounted_products (
                    discounted_product_uuid,
                    real_price,
                    discounted_price,
                    name,
                    url,
                    category_uuid,
                    retailer_uuid,
                    created_at,
                    updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor: CursorWrapper
            with connection.cursor() as cursor:
                cursor.executemany(
                    insert_query,
                    [
                        (
                            discounted_product.get_uuid(),
                            discounted_product.get_real_price(),
                            discounted_product.get_discounted_price(),
                            discounted_product.get_name(),
                            discounted_product.get_url(),
                            discounted_product.get_category_uuid() if discounted_product.has_category() else None,
                            discounted_product.get_retailer_uuid(),
                            discounted_product.get_created_at(),
                            discounted_product.get_updated_at(),
                        )
                        for discounted_product in _discounted_products
                    ],
                )

        return await sync_to_async(_sync_version)(discounted_products)

    @override
    async def _get_by_uuid(self, uuid_: UUID) -> DiscountedProduct | None:
        def _sync_version(_discounted_product_uuid: UUID) -> DiscountedProduct | None:
            select_query = """
                SELECT
                    real_price,
                    discounted_price,
                    name,
                    url,
                    category_uuid,
                    retailer_uuid,
                    created_at,
                    updated_at
                FROM discounted_products dp
                WHERE dp.discounted_product_uuid = %s;
            """
            cursor: CursorWrapper
            with connection.cursor() as cursor:
                cursor.execute(select_query, [_discounted_product_uuid])
                row = cursor.fetchone()
                if row is not None:
                    return DiscountedProduct(
                        uuid_=_discounted_product_uuid,
                        real_price=row[0],
                        discounted_price=row[1],
                        name=row[2],
                        url=row[3],
                        category_uuid=row[4],
                        retailer_uuid=row[5],
                        created_at=row[6],
                        updated_at=row[7],
                    )
            return None

        return await sync_to_async(_sync_version)(uuid_)

    @override
    async def delete_older_than_and_return_deleted_count(self, date_limit: datetime) -> int:
        def _sync_version(_date_limit: datetime) -> int:
            delete_query = """
                DELETE FROM discounted_products
                WHERE created_at < %s
            """
            cursor: CursorWrapper
            with connection.cursor() as cursor:
                cursor.execute(delete_query, [date_limit])

                return int(cursor.rowcount)

        return await sync_to_async(_sync_version)(date_limit)

    @override
    async def get_all(self, chunk_size: int = 500) -> AsyncIterator[DiscountedProduct]:
        offset = 0
        while True:
            discounted_products: list[DiscountedProduct] = await sync_to_async(self.__fetch_chunk)(
                offset, chunk_size
            )
            for discounted_product in discounted_products:
                yield discounted_product
            if len(discounted_products) < chunk_size:
                break
            offset += chunk_size

    @override
    async def get_all_by_date(
        self, date_: datetime, chunk_size: int = 500
    ) -> AsyncIterator[DiscountedProductWithDetails]:
        offset = 0
        while True:
            discounted_products_with_details = await sync_to_async(self.__fetch_chunk_by_created_at)(
                date_, offset, chunk_size
            )
            for discounted_product_with_details in discounted_products_with_details:
                yield discounted_product_with_details
            if len(discounted_products_with_details) < chunk_size:
                break
            offset += chunk_size

    @staticmethod
    def __fetch_chunk_by_created_at(
        created_at: datetime, offset: int, limit: int
    ) -> list[DiscountedProductWithDetails]:
        cursor: CursorWrapper
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    dp.discounted_product_uuid,
                    dp.real_price,
                    dp.discounted_price,
                    dp.name,
                    dp.url,
                    dp.category_uuid,
                    dp.retailer_uuid,
                    dp.created_at,
                    dp.updated_at,
                    c.name,
                    r.name
                FROM discounted_products dp
                LEFT JOIN categories c ON dp.category_uuid = c.category_uuid
                LEFT JOIN retailers r ON dp.retailer_uuid = r.retailer_uuid
                WHERE dp.created_at = %s
                ORDER BY dp.discounted_product_uuid
                LIMIT %s OFFSET %s
                """,
                [created_at, limit, offset],
            )
            rows: list[
                tuple[
                    UUID,
                    Decimal,
                    Decimal,
                    str,
                    str,
                    CategoryUUID,
                    RetailerUUID,
                    datetime,
                    datetime,
                    CategoryName,
                    RetailerName,
                ]
            ] = cursor.fetchall()
            return [
                DiscountedProductWithDetails(
                    category_name=row[9],
                    retailer_name=row[10],
                    entity=DiscountedProduct(
                        uuid_=row[0],
                        real_price=row[1],
                        discounted_price=row[2],
                        name=row[3],
                        url=row[4],
                        category_uuid=row[5],
                        retailer_uuid=row[6],
                        created_at=row[7],
                        updated_at=row[8],
                    ),
                )
                for row in rows
            ]

    @staticmethod
    def __fetch_chunk(offset: int, limit: int) -> list[DiscountedProduct]:
        cursor: CursorWrapper
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    discounted_product_uuid,
                    real_price,
                    discounted_price,
                    name,
                    url,
                    category_uuid,
                    retailer_uuid,
                    created_at,
                    updated_at
                FROM discounted_products
                ORDER BY discounted_product_uuid
                LIMIT %s OFFSET %s
                """,
                [limit, offset],
            )
            rows: list[tuple[UUID, Decimal, Decimal, str, str, CategoryUUID, RetailerUUID, datetime, datetime]] = (
                cursor.fetchall()
            )
            return [
                DiscountedProduct(
                    uuid_=row[0],
                    real_price=row[1],
                    discounted_price=row[2],
                    name=row[3],
                    url=row[4],
                    category_uuid=row[5],
                    retailer_uuid=row[6],
                    created_at=row[7],
                    updated_at=row[8],
                )
                for row in rows
            ]
