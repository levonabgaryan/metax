from __future__ import annotations

from typing import override

from django.db import models
from django_stubs_ext.db.models import TypedModelMeta

from metax.core.domain.entities.retailer.value_objects import RetailersNames

from .base_model import BaseDbModel


def retailer_name_choices() -> list[tuple[str, str]]:
    """Build the admin's retailer-name dropdown from the ``RetailersNames`` enum.

    Passed to ``choices`` as a callable, not as an evaluated tuple: Django serializes a callable
    into migrations by dotted reference rather than by value, so onboarding a retailer (adding an
    enum member) no longer makes the model diverge from migration state. Choices are validation-only
    and map to no DDL, so there is nothing for a per-retailer migration to do anyway.

    Returns:
        One ``(value, label)`` pair per member, both set to the slug.
    """
    return [(member.value, member.value) for member in RetailersNames]


class RetailerModel(BaseDbModel):
    uuid = models.UUIDField(primary_key=True, editable=False)
    name = models.CharField(max_length=64, unique=True, null=False, choices=retailer_name_choices)
    home_page_url = models.URLField(max_length=2048)
    phone_number = models.CharField(max_length=64)
    # When set, every product collected from this retailer is stamped with this category directly
    # (skipping the embedding classifier) — for retailers whose whole catalog is a single category.
    default_category = models.ForeignKey(
        "CategoryModel",
        on_delete=models.SET_NULL,
        db_column="default_category_uuid",
        related_name="+",
        null=True,
        blank=True,
    )

    class Meta(TypedModelMeta):
        db_table = "retailers"
        verbose_name = "retailer"
        verbose_name_plural = "retailers"

    @override
    def __str__(self) -> str:
        return f"{self.name} ({self.uuid})"
