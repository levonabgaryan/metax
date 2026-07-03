"""Seed the tntesakan.am retailer with a fixed default category.

tntesakan.am ("տնտեսական" — household goods) is configured with ``default_category`` = Home & Garden.
Because that category is fixed, the collection use case stamps every product it collects with it and
skips the embedding classifier entirely — no per-product embedding is spent on identifying it.

Like the category seed, the UUID is hardcoded (a valid version-7 UUID, which the domain ``Retailer``
requires when the row is loaded) so the migration is deterministic and idempotent: re-applying inserts
nothing new. ``created_at``/``updated_at`` are left to their DB defaults (``Now()``).
"""

from __future__ import annotations

from django.db import migrations

_RETAILER_UUID = "019f240a-7b67-7026-a46b-bb5e68a1fbe2"
_RETAILER_NAME = "tntesakan-am"
_RETAILER_HOME_PAGE_URL = "https://tntesakan.am"
_RETAILER_PHONE_NUMBER = "+374 98 849090"
# Home & Garden — see 0002_seed_categories.
_HOME_AND_GARDEN_CATEGORY_UUID = "019f006f-6337-7234-a483-532df5e61e09"


def _seed_retailer(apps, schema_editor) -> None:
    retailer_model = apps.get_model("metax", "RetailerModel")
    retailer_model.objects.update_or_create(
        uuid=_RETAILER_UUID,
        defaults={
            "name": _RETAILER_NAME,
            "home_page_url": _RETAILER_HOME_PAGE_URL,
            "phone_number": _RETAILER_PHONE_NUMBER,
            "default_category_id": _HOME_AND_GARDEN_CATEGORY_UUID,
        },
    )


def _unseed_retailer(apps, schema_editor) -> None:
    retailer_model = apps.get_model("metax", "RetailerModel")
    retailer_model.objects.filter(uuid=_RETAILER_UUID).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("metax", "0004_retailermodel_default_category_and_more"),
    ]

    operations = [
        migrations.RunPython(_seed_retailer, _unseed_retailer),
    ]
