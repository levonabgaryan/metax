from __future__ import annotations
from django_stubs_ext.db.models import TypedModelMeta

from django.db import models
from django.contrib.postgres.indexes import GinIndex

from .base_model import BaseDbModel


class CategoryHelperWordsModel(BaseDbModel):
    id = models.AutoField(primary_key=True)
    word = models.CharField(max_length=64, unique=True)
    category = models.ForeignKey("CategoryModel", on_delete=models.CASCADE, db_column="category_uuid", null=False)

    class Meta(TypedModelMeta):
        db_table = "category_helper_words"
        verbose_name = "category helper word"
        verbose_name_plural = "category helper words"
        indexes = [
            GinIndex(
                fields=["word"],
                name="helper_word_trgm_idx",
                opclasses=["gin_trgm_ops"],
            ),
        ]

    def __str__(self) -> str:
        return self.word
