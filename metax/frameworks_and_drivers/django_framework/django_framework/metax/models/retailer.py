from __future__ import annotations

from typing import override

from django.db import models
from django_stubs_ext.db.models import TypedModelMeta

from metax.core.domain.entities.retailer.value_objects import RetailersNames

from .base_model import BaseDbModel

_RETAILER_NAME_CHOICES = tuple((member.value, member.value) for member in RetailersNames)


class RetailerModel(BaseDbModel):
    retailer_uuid = models.UUIDField(primary_key=True, editable=False)
    name = models.CharField(max_length=64, unique=True, null=False, choices=_RETAILER_NAME_CHOICES)
    url = models.URLField(max_length=2048)
    phone_number = models.CharField(max_length=64)

    class Meta(TypedModelMeta):
        db_table = "retailers"
        verbose_name = "retailer"
        verbose_name_plural = "retailers"

    @override
    def __str__(self) -> str:
        return f"{self.name} ({self.retailer_uuid})"
