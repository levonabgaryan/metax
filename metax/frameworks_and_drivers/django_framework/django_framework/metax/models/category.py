from __future__ import annotations

from typing import override

from django_stubs_ext.db.models import TypedModelMeta

from django.db import models

from .base_model import BaseDbModel


class CategoryModel(BaseDbModel):
    category_uuid = models.UUIDField(primary_key=True, editable=False)
    name = models.CharField(unique=True, max_length=64, null=False)

    class Meta(TypedModelMeta):
        db_table = "categories"
        verbose_name = "category"
        verbose_name_plural = "categories"

    @override
    def __str__(self) -> str:
        return f"{self.name} ({self.category_uuid})"
