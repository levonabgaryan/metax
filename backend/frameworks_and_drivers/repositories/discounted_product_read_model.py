from datetime import datetime


from backend.core.application.ports.repositories.discounted_product_read_model import (
    DiscountedProductReadModelRepository,
)
from backend.core.domain.entities.category_entity.category import Category
from backend.core.domain.entities.retailer_entity.retailer import Retailer
from django_framework.discount_service.models import DiscountedProductReadModel

from django_framework.discount_service.models import DiscountedProductModel


class DjangoSqlLiteDiscountedProductReadModelRepository(DiscountedProductReadModelRepository):
    @staticmethod
    async def sync_many_by_date(date: datetime) -> None:
        source_queryset = DiscountedProductModel._default_manager.filter(
            created_at=date,
        ).select_related("category", "retailer")

        new_entries = []
        async for p in source_queryset.aiterator():
            new_entries.append(
                DiscountedProductReadModel(
                    discounted_product_uuid=p.discounted_product_uuid,
                    real_price=p.real_price,
                    discounted_price=p.discounted_price,
                    name=p.name,
                    url=p.url,
                    category_uuid=p.category.category_uuid if p.category else None,
                    category_name=p.category.name if p.category else None,
                    retailer_uuid=p.retailer.retailer_uuid,
                    retailer_name=p.retailer.name,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                )
            )

        if new_entries:
            await DiscountedProductReadModel._default_manager.abulk_create(new_entries)

    async def delete_older_than_and_return_deleted_count(self, date_limit: datetime) -> int:
        queryset = DiscountedProductReadModel._default_manager.filter(created_at__lt=date_limit)
        count, _ = await queryset.adelete()
        return count

    async def update_category(self, updated_category: Category) -> None:
        await DiscountedProductReadModel._default_manager.filter(
            category_uuid=updated_category.get_uuid()
        ).aupdate(category_name=updated_category.get_name())

    async def update_retailer(self, updated_retailer: Retailer) -> None:
        await DiscountedProductReadModel._default_manager.filter(
            retailer_uuid=updated_retailer.get_uuid()
        ).aupdate(retailer_name=updated_retailer.get_name())
