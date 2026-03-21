from datetime import datetime
from typing import AsyncIterator, override
from uuid import UUID

from django.db.models import QuerySet

from metax.core.application.ports.repositories.entites_repositories.discounted_product import (
    DiscountedProductRepository,
    DiscountedProductWithDetails,
)
from metax.core.domain.entities.discounted_product_entity.discounted_product import (
    DiscountedProduct,
    PriceDetails,
)
from django_framework.metax.models import (
    DiscountedProductModel,
)


class DjangoPostgresqlDiscountedProductRepository(DiscountedProductRepository):
    @override
    async def add_many(self, discounted_products: list[DiscountedProduct]) -> None:
        models = [
            DiscountedProductModel(
                discounted_product_uuid=product.get_uuid(),
                real_price=product.get_real_price(),
                discounted_price=product.get_discounted_price(),
                name=product.get_name(),
                url=product.get_url(),
                category_id=product.get_category_uuid() if product.has_category() else None,
                retailer_id=product.get_retailer_uuid(),
                created_at=product.get_created_at(),
            )
            for product in discounted_products
        ]
        await DiscountedProductModel._default_manager.abulk_create(models)

    @override
    async def _get_by_uuid(self, discounted_product_uuid: UUID) -> DiscountedProduct | None:
        try:
            discounted_product_model = await DiscountedProductModel._default_manager.select_related(
                "category", "retailer"
            ).aget(discounted_product_uuid=discounted_product_uuid)
        except DiscountedProductModel.DoesNotExist:
            return None

        return self.__convert_django_model_to_entity(discounted_product_model)

    @override
    async def delete_older_than_and_return_deleted_count(self, date_limit: datetime) -> int:
        deleted_count, _ = await DiscountedProductModel._default_manager.filter(
            created_at__lt=date_limit
        ).adelete()

        return deleted_count

    @override
    async def get_all(self) -> AsyncIterator[DiscountedProduct]:
        queryset = DiscountedProductModel._default_manager.select_related("category", "retailer").all()
        async for model in queryset.aiterator(chunk_size=100):
            yield self.__convert_django_model_to_entity(model)

    @override
    async def get_all_by_date(self, date_: datetime) -> AsyncIterator[DiscountedProductWithDetails]:
        queryset: QuerySet[DiscountedProductModel, DiscountedProductModel] = (
            DiscountedProductModel._default_manager.select_related("category", "retailer").filter(created_at=date_)
        )
        model: DiscountedProductModel
        async for model in queryset.aiterator(chunk_size=100):
            entity: DiscountedProduct = self.__convert_django_model_to_entity(model)
            yield DiscountedProductWithDetails(
                entity=entity,
                category_name=model.category.name if model.category is not None else None,
                retailer_name=model.retailer.name,
            )

    @staticmethod
    def __convert_django_model_to_entity(model: DiscountedProductModel) -> DiscountedProduct:
        return DiscountedProduct(
            discounted_product_uuid=model.discounted_product_uuid,
            name=model.name,
            url=model.url,
            price_details=PriceDetails(real_price=model.real_price, discounted_price=model.discounted_price),
            category_uuid=model.category.category_uuid if model.category else None,
            retailer_uuid=model.retailer.retailer_uuid,
            created_at=model.created_at,
        )
