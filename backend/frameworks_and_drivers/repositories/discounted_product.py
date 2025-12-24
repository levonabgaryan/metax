from uuid import UUID

from backend.core.application.input_ports.repositories.discounted_product import DiscountedProductRepository
from backend.core.domain.entities.discounted_product_entity.discounted_product import (
    DiscountedProduct,
    PriceDetails,
)
from django_framework.discount_service.models import (
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

    async def _get_by_uuid(self, discounted_product_uuid: UUID) -> DiscountedProduct | None:
        try:
            discounted_product_model = await DiscountedProductModel._default_manager.select_related(
                "category", "retailer"
            ).aget(discounted_product_uuid=discounted_product_uuid)
        except DiscountedProductModel.DoesNotExist:
            return None

        return self.__map_to_entity(discounted_product_model)

    @staticmethod
    def __map_to_entity(model: DiscountedProductModel) -> DiscountedProduct:
        return DiscountedProduct(
            discounted_product_uuid=model.discounted_product_uuid,
            name=model.name,
            url=model.url,
            price_details=PriceDetails(real_price=model.real_price, discounted_price=model.discounted_price),
            category_uuid=model.category.category_uuid,
            retailer_uuid=model.retailer.retailer_uuid,
        )
