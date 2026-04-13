from datetime import datetime
from decimal import Decimal
from typing import AsyncIterator, override
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
from metax.core.domain.entities.discounted_product.value_objects import PriceDetails

type CategoryUUID = UUID
type RetailerUUID = UUID
type CategoryName = str
type RetailerName = str


class DjangoPostgresqlDiscountedProductRepository(DiscountedProductRepository):
    @override
    async def add_many(self, discounted_products: list[DiscountedProduct]) -> None:
        def _sync_version(_discounted_products: list[DiscountedProduct]) -> None:
            _insert_query = """
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
            _cursor: CursorWrapper
            with connection.cursor() as _cursor:
                _cursor.executemany(
                    _insert_query,
                    [
                        (
                            _discounted_product.get_uuid(),
                            _discounted_product.get_real_price(),
                            _discounted_product.get_discounted_price(),
                            _discounted_product.get_name(),
                            _discounted_product.get_url(),
                            _discounted_product.get_category_uuid()
                            if _discounted_product.has_category()
                            else None,
                            _discounted_product.get_retailer_uuid(),
                            _discounted_product.get_created_at(),
                            _discounted_product.get_updated_at(),
                        )
                        for _discounted_product in _discounted_products
                    ],
                )

        return await sync_to_async(_sync_version)(discounted_products)

    @override
    async def _get_by_uuid(self, discounted_product_uuid: UUID) -> DiscountedProduct | None:
        def _sync_version(_discounted_product_uuid: UUID) -> DiscountedProduct | None:
            _select_query = """
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
            _cursor: CursorWrapper
            with connection.cursor() as _cursor:
                _cursor.execute(_select_query, [discounted_product_uuid])
                row = _cursor.fetchone()
                if row is not None:
                    return DiscountedProduct(
                        discounted_product_uuid=_discounted_product_uuid,
                        price_details=PriceDetails(
                            real_price=row[0],
                            discounted_price=row[1],
                        ),
                        name=row[2],
                        url=row[3],
                        category_uuid=row[4],
                        retailer_uuid=row[5],
                        created_at=row[6],
                        updated_at=row[7],
                    )
            return None

        return await sync_to_async(_sync_version)(discounted_product_uuid)

    @override
    async def delete_older_than_and_return_deleted_count(self, date_limit: datetime) -> int:
        def _sync_version(_date_limit: datetime) -> int:
            _delete_query = """
                DELETE FROM discounted_products
                WHERE created_at < %s
            """
            _cursor: CursorWrapper
            with connection.cursor() as _cursor:
                _cursor.execute(_delete_query, [date_limit])

                return int(_cursor.rowcount)

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
        _cursor: CursorWrapper
        with connection.cursor() as _cursor:
            _cursor.execute(
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
            ] = _cursor.fetchall()
            return [
                DiscountedProductWithDetails(
                    category_name=row[9],
                    retailer_name=row[10],
                    entity=DiscountedProduct(
                        discounted_product_uuid=row[0],
                        price_details=PriceDetails(
                            real_price=row[1],
                            discounted_price=row[2],
                        ),
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
        _cursor: CursorWrapper
        with connection.cursor() as _cursor:
            _cursor.execute(
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
                _cursor.fetchall()
            )
            return [
                DiscountedProduct(
                    discounted_product_uuid=row[0],
                    price_details=PriceDetails(
                        real_price=row[1],
                        discounted_price=row[2],
                    ),
                    name=row[3],
                    url=row[4],
                    category_uuid=row[5],
                    retailer_uuid=row[6],
                    created_at=row[7],
                    updated_at=row[8],
                )
                for row in rows
            ]
