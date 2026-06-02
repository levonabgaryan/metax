from __future__ import annotations

from typing import override

from django.db import models
from django_stubs_ext.db.models import TypedModelMeta

from .base_model import BaseDbModel


class CategoryModel(BaseDbModel):
    uuid = models.UUIDField(primary_key=True, editable=False)
    name = models.CharField(unique=True, max_length=64, null=False)
    name_hy = models.CharField(max_length=128, blank=True, default="")
    name_ru = models.CharField(max_length=128, blank=True, default="")

    class Meta(TypedModelMeta):
        db_table = "categories"
        verbose_name = "category"
        verbose_name_plural = "categories"

    @override
    def __str__(self) -> str:
        return f"{self.name} ({self.uuid})"
