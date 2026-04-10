from __future__ import annotations

from typing import override

from django.db import models
from django_stubs_ext.db.models import TypedModelMeta

from .base_model import BaseDbModel


class CategoryHelperWordsModel(BaseDbModel):
    id = models.AutoField(primary_key=True)
    word = models.CharField(max_length=64, unique=True)
    category = models.ForeignKey("CategoryModel", on_delete=models.CASCADE, db_column="category_uuid", null=False)

    class Meta(TypedModelMeta):
        db_table = "category_helper_words"
        verbose_name = "category helper word"
        verbose_name_plural = "category helper words"

    @override
    def __str__(self) -> str:
        return self.word
