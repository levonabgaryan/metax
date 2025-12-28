from __future__ import annotations


from django_stubs_ext.db.models import TypedModelMeta

from django.db import models

from .base_model import BaseDbModel


class DiscountedProductModel(BaseDbModel):
    discounted_product_uuid = models.UUIDField(primary_key=True, editable=False)
    real_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    name = models.CharField(max_length=64, null=False)
    url = models.URLField(max_length=2048)

    category = models.ForeignKey("CategoryModel", on_delete=models.SET_NULL, db_column="category_uuid", null=True)
    retailer = models.ForeignKey("RetailerModel", on_delete=models.CASCADE, db_column="retailer_uuid")

    created_at = models.DateTimeField()

    class Meta(TypedModelMeta):
        db_table = "discounted_products"
        verbose_name = "discounted product"
        verbose_name_plural = "discounted products"

    def __str__(self) -> str:
        return f"{self.name} ({self.discounted_product_uuid})"
