from __future__ import annotations

from typing import override

from django.db import models
from django_stubs_ext.db.models import TypedModelMeta

from .base_model import BaseDbModel


class CategoryHelperWordsModel(BaseDbModel):
    helper_word_uuid = models.UUIDField(primary_key=True, editable=False)
    helper_word_text = models.CharField(max_length=128, unique=True, null=False)
    category = models.ForeignKey("CategoryModel", on_delete=models.CASCADE, db_column="category_uuid", null=False)

    class Meta(TypedModelMeta):
        db_table = "category_helper_words"
        verbose_name = "category helper word"
        verbose_name_plural = "category helper words"

    @override
    def __str__(self) -> str:
        return self.helper_word_text
