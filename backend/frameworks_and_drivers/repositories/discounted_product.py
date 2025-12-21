from backend.core.application.ports.repositories.discounted_product import DiscountedProductRepository
from backend.core.domain.entities.discounted_product_entity.discounted_product import DiscountedProduct
from backend.frameworks_and_drivers.django_framework.django_framework.discount_service.models import (
    DiscountedProductModel,
)


class DjangoSqlLiteDiscountedProductRepository(DiscountedProductRepository):
    async def add_many(self, discounted_products: list[DiscountedProduct]) -> None:
        models = [
            DiscountedProductModel(
                discounted_product_uuid=product.get_uuid(),
                real_price=product.get_real_price(),
                discounted_price=product.get_discounted_price(),
                name=product.get_name(),
                url=product.get_url(),
                category_id=product.get_category_uuid(),
                retailer_id=product.get_retailer_uuid(),
            )
            for product in discounted_products
        ]
        await DiscountedProductModel._default_manager.abulk_create(models)
