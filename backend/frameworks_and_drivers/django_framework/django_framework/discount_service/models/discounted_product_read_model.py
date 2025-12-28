from django.db import models
from django_stubs_ext.db.models import TypedModelMeta

from .base_model import BaseDbModel


class DiscountedProductReadModel(BaseDbModel):
    discounted_product_uuid = models.UUIDField(primary_key=True)
    real_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    name = models.CharField(max_length=64)
    url = models.URLField(max_length=2048)

    category_uuid = models.UUIDField(null=True)
    category_name = models.CharField(max_length=128, null=True)

    retailer_uuid = models.UUIDField()
    retailer_name = models.CharField(max_length=128)

    class Meta(TypedModelMeta):
        db_table = "discounted_products_read_model"
        verbose_name = "discounted product read model"
        verbose_name_plural = "discounted products read models"

    def __str__(self) -> str:
        return f"{self.name} ({self.discounted_product_uuid})"
