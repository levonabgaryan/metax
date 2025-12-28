from datetime import datetime

from asgiref.sync import sync_to_async

from backend.core.application.ports.repositories.discounted_product_read_model import (
    DiscountedProductReadModelRepository,
)
from backend.core.domain.entities.category_entity.category import Category
from backend.core.domain.entities.retailer_entity.retailer import Retailer
from django_framework.discount_service.models import DiscountedProductReadModel
from django.db import connection

from django_framework.discount_service.models import DiscountedProductModel, CategoryModel, RetailerModel


class DjangoSqlLiteDiscountedProductReadModelRepository(DiscountedProductReadModelRepository):
    @staticmethod
    def __add_many_by_date(date: datetime) -> None:
        formatted_date = date.strftime("%Y-%m-%d %H:%M:%S")
        query = f"""
                INSERT INTO {DiscountedProductReadModel._meta.db_table} (
                    discounted_product_uuid, real_price, discounted_price, 
                    name, url, category_uuid, category_name, 
                    retailer_uuid, retailer_name, created_at, updated_at
                )
                SELECT 
                    p.discounted_product_uuid, 
                    p.real_price, 
                    p.discounted_price, 
                    p.name, 
                    p.url, 
                    p.category_uuid,
                    c.name as category_name, 
                    p.retailer_uuid, 
                    r.name as retailer_name, 
                    p.created_at, 
                    p.updated_at
                FROM {DiscountedProductModel._meta.db_table} p
                LEFT JOIN {CategoryModel._meta.db_table} c ON p.category_uuid = c.category_uuid
                INNER JOIN {RetailerModel._meta.db_table} r ON p.retailer_uuid = r.retailer_uuid
                WHERE strftime('%Y-%m-%d %H:%M:%S', p.created_at) = %s
        """
        with connection.cursor() as cursor:
            cursor.execute(query, [formatted_date])

    async def add_many_by_date(self, date: datetime) -> None:
        await sync_to_async(self.__add_many_by_date, thread_sensitive=True)(date)

    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def __delete_older_than(date_limit: datetime) -> int:
        query = f"""
            DELETE FROM {DiscountedProductReadModel._meta.db_table}
            WHERE created_at < %s
        """
        with connection.cursor() as cursor:
            cursor.execute(query, [date_limit])
            count = cursor.rowcount
            return int(count) if count is not None else 0

    async def delete_older_than_and_return_deleted_count(self, date_limit: datetime) -> int:
        return await self.__delete_older_than(date_limit)

    async def update_category(self, updated_category: Category) -> None:
        return await self.__update_category(updated_category)

    async def update_retailer(self, updated_retailer: Retailer) -> None:
        return await self.__update_retailer(updated_retailer)

    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def __update_category(updated_category: Category) -> None:
        query = f"""
                UPDATE {DiscountedProductReadModel._meta.db_table}
                SET category_name = %s
                WHERE category_uuid = %s
            """
        with connection.cursor() as cursor:
            cursor.execute(query, [updated_category.get_name(), updated_category.get_uuid()])

    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def __update_retailer(updated_retailer: Retailer) -> None:
        query = f"""
                UPDATE {DiscountedProductReadModel._meta.db_table}
                SET retailer_name = %s
                WHERE retailer_uuid = %s
            """
        with connection.cursor() as cursor:
            cursor.execute(query, [updated_retailer.get_name(), updated_retailer.get_uuid()])
