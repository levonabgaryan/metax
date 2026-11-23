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
    # Example product names (one per line or comma-separated) that anchor this category for the
    # embedding classifier. Edit here to teach the classifier new words for a category.
    examples = models.TextField(
        blank=True,
        default="",
        help_text="Example product names for auto-categorization — one per line or comma-separated.",
    )
    # Exact keyword phrases (one per line or comma-separated). A product whose name — the part before
    # the brand in «…» — contains one of these words is assigned this category outright, before any
    # embedding similarity is considered. A phrase may belong to only one category.
    keywords = models.TextField(
        blank=True,
        default="",
        help_text=(
            "Exact keywords, one per line. A product whose name (before the «brand») contains one is put in "
            "this category with full confidence. Words of 4+ letters also match longer word forms "
            "(շոկոլադ → շոկոլադե). The longest matching phrase wins, so add a phrase like "
            "«միցելային ջուր» to override a single word like «ջուր». Each keyword may belong to one "
            "category only."
        ),
    )

    class Meta(TypedModelMeta):
        db_table = "categories"
        verbose_name = "category"
        verbose_name_plural = "categories"

    @override
    def __str__(self) -> str:
        return f"{self.name} ({self.uuid})"
