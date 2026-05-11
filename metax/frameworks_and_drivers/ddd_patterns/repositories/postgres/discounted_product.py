import datetime as dt
from collections.abc import AsyncIterator
from decimal import Decimal
from typing import override
from uuid import UUID

from asgiref.sync import sync_to_async
from django.db import IntegrityError, connection
from django.db.backends.utils import CursorWrapper

from metax.core.application.ports.ddd_patterns.repository.entites_repositories.discounted_product import (
    DiscountedProductRepository,
    DiscountedProductWithRelations,
)
from metax.core.application.ports.ddd_patterns.repository.errors import EntityAlreadyExistsError
from metax.core.domain.entities.category.aggregate_root_entity import Category
from metax.core.domain.entities.discounted_product.aggregate_root_entity import (
    DiscountedProduct,
)
from metax.core.domain.entities.retailer.aggregate_root_entity import Retailer
from metax.frameworks_and_drivers.ddd_patterns.repositories.postgres.utils import (
    extract_field_from_integrity_message,
)

type CategoryUUID = UUID | None
type RetailerUUID = UUID


class DjangoPostgresqlDiscountedProductRepository(DiscountedProductRepository):
    @override
    async def all(self, chunk_size: int = 500) -> AsyncIterator[DiscountedProduct]:
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
    async def delete_older_than_and_return_deleted_count(self, date_limit: dt.datetime) -> int:
        def _sync_version(_date_limit: dt.datetime) -> int:
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
    async def delete_by_retailer_uuid_and_return_deleted_count(self, retailer_uuid: UUID) -> int:
        def _sync_version(_retailer_uuid: UUID) -> int:
            delete_query = """
                DELETE FROM discounted_products
                WHERE retailer_uuid = %s
            """
            cursor: CursorWrapper
            with connection.cursor() as cursor:
                cursor.execute(delete_query, [_retailer_uuid])
                return int(cursor.rowcount)

        return await sync_to_async(_sync_version)(retailer_uuid)

    @override
    async def delete_category_by_uuid(self, category_uuid: UUID) -> int:
        def _sync_version(_category_uuid: UUID) -> int:
            update_query = """
                UPDATE discounted_products
                SET category_uuid = NULL
                WHERE category_uuid = %s
            """
            cursor: CursorWrapper
            with connection.cursor() as cursor:
                cursor.execute(update_query, [_category_uuid])
                return int(cursor.rowcount)

        return await sync_to_async(_sync_version)(category_uuid)

    @override
    async def get_by_created_at(
        self, created_at: dt.datetime, chunk_size: int = 500
    ) -> AsyncIterator[DiscountedProductWithRelations]:
        offset = 0
        while True:
            discounted_products: list[DiscountedProductWithRelations] = await sync_to_async(
                self.__fetch_chunk_by_created_at
            )(created_at, offset, chunk_size)
            for discounted_product in discounted_products:
                yield discounted_product
            if len(discounted_products) < chunk_size:
                break
            offset += chunk_size

    @override
    async def _add_many(self, discounted_products: list[DiscountedProduct]) -> None:
        def _sync_version(_discounted_products: list[DiscountedProduct]) -> None:
            insert_query = """
                INSERT INTO discounted_products (
                    uuid,
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

        try:
            return await sync_to_async(_sync_version)(discounted_products)
        except IntegrityError as err:
            field_name, field_value = extract_field_from_integrity_message(str(err))
            raise EntityAlreadyExistsError(
                entity_type="discounted_product",
                entity_field_name=field_name,
                entity_field_value=field_value,
            ) from err

    @override
    async def _get_by_uuid(self, uuid_: UUID) -> DiscountedProduct | None:
        def _sync_version(_uuid: UUID) -> DiscountedProduct | None:
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
                WHERE dp.uuid = %s;
            """
            cursor: CursorWrapper
            with connection.cursor() as cursor:
                cursor.execute(select_query, [_uuid])
                row = cursor.fetchone()
                if row is not None:
                    return DiscountedProduct(
                        uuid_=_uuid,
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

    @staticmethod
    def __fetch_chunk(offset: int, limit: int) -> list[DiscountedProduct]:
        cursor: CursorWrapper
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    uuid,
                    real_price,
                    discounted_price,
                    name,
                    url,
                    category_uuid,
                    retailer_uuid,
                    created_at,
                    updated_at
                FROM discounted_products
                ORDER BY uuid
                LIMIT %s OFFSET %s
                """,
                [limit, offset],
            )
            rows: list[
                tuple[UUID, Decimal, Decimal, str, str, CategoryUUID, RetailerUUID, dt.datetime, dt.datetime]
            ] = cursor.fetchall()
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

    @staticmethod
    def __fetch_chunk_by_created_at(
        created_at: dt.datetime, offset: int, limit: int
    ) -> list[DiscountedProductWithRelations]:
        cursor: CursorWrapper
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    dp.uuid,
                    dp.real_price,
                    dp.discounted_price,
                    dp.name,
                    dp.url,
                    dp.category_uuid,
                    dp.retailer_uuid,
                    dp.created_at,
                    dp.updated_at,
                    c.uuid,
                    c.created_at,
                    c.updated_at,
                    c.name,
                    r.created_at,
                    r.updated_at,
                    r.name,
                    r.home_page_url,
                    r.phone_number
                FROM discounted_products dp
                LEFT JOIN categories c ON dp.category_uuid = c.uuid
                INNER JOIN retailers r ON dp.retailer_uuid = r.uuid
                WHERE date_trunc('microseconds', dp.created_at)
                    = date_trunc('microseconds', CAST(%s AS TIMESTAMPTZ))
                ORDER BY dp.uuid
                LIMIT %s OFFSET %s
                """,
                [created_at, limit, offset],
            )
            rows = cursor.fetchall()
            result: list[DiscountedProductWithRelations] = []
            for row in rows:
                (
                    dp_uuid,
                    real_price,
                    discounted_price,
                    dp_name,
                    url,
                    category_uuid,
                    retailer_uuid,
                    dp_created_at,
                    dp_updated_at,
                    cat_uuid,
                    cat_created_at,
                    cat_updated_at,
                    cat_name,
                    ret_created_at,
                    ret_updated_at,
                    ret_name,
                    ret_home_page_url,
                    ret_phone_number,
                ) = row
                entity = DiscountedProduct(
                    uuid_=dp_uuid,
                    real_price=real_price,
                    discounted_price=discounted_price,
                    name=dp_name,
                    url=url,
                    category_uuid=category_uuid,
                    retailer_uuid=retailer_uuid,
                    created_at=dp_created_at,
                    updated_at=dp_updated_at,
                )
                retailer = Retailer(
                    uuid_=retailer_uuid,
                    created_at=ret_created_at,
                    updated_at=ret_updated_at,
                    name=ret_name,
                    home_page_url=ret_home_page_url,
                    phone_number=ret_phone_number,
                )
                category: Category | None = None
                if cat_uuid is not None and cat_created_at is not None and cat_updated_at is not None:
                    category = Category(
                        uuid_=cat_uuid,
                        created_at=cat_created_at,
                        updated_at=cat_updated_at,
                        helper_words=[],
                        name=cat_name,
                    )
                result.append(DiscountedProductWithRelations(entity=entity, retailer=retailer, category=category))
            return result
