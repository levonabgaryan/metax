"""Seed the initial product categories.

Categories must exist for embedding-based classification to assign anything (the classifier
loads them at crawl time and skips when there are none). Each row carries English/Armenian/
Russian names so the classifier can embed all three localized labels per category.

UUIDs are hardcoded (and are valid version-7 UUIDs, which the domain ``Category`` requires on
load) so the migration is deterministic and idempotent: re-applying inserts nothing new and the
same products keep pointing at the same category rows. ``created_at``/``updated_at`` are left to
their DB defaults (``Now()``).
"""

from __future__ import annotations

from django.db import migrations

# (uuid, name, name_hy, name_ru)
_CATEGORIES = [
    ("019f006f-6337-7234-a483-53294ab7215e", "Groceries & Food", "Սննդամթերք", "Продукты питания"),
    ("019f006f-6337-7234-a483-532ae1279221", "Drinks & Alcohol", "Ըմպելիքներ և Ալկոհոլ", "Напитки и Алкоголь"),
    ("019f006f-6337-7234-a483-532bacead220", "Electronics & Appliances", "Էլեկտրոնիկա և Կենցաղային տեխնիկա", "Электроника и Техника"),
    ("019f006f-6337-7234-a483-532c1117974f", "Clothing, Shoes & Fashion", "Հագուստ և Կոշիկ", "Одежда, Обувь и Мода"),
    ("019f006f-6337-7234-a483-532df5e61e09", "Home & Garden", "Տուն և Այգի", "Дом и Сад"),
    ("019f006f-6337-7234-a483-532e26922575", "Health & Beauty", "Առողջություն և Գեղեցկություն", "Здоровье и Красота"),
    ("019f006f-6337-7234-a483-532fff506c77", "Children & Baby Products", "Մանկական ապրանքներ", "Детские товары"),
    ("019f006f-6337-7234-a483-53309db9ae74", "Pet Supplies", "Կենդանիների խնամք", "Товары для животных"),
    ("019f006f-6337-7234-a483-5331e4f969ca", "Automotive & Tools", "Ավտոապրանքներ և Գործիքներ", "Автотовары и Инструменты"),
    ("019f006f-6337-7234-a483-5332b813b6c7", "Stationery, Books & Hobbies", "Գրենական պիտույքներ և Հոբբի", "Канцтовары, Книги и Хобби"),
    ("019f006f-6337-7234-a483-53337b0550a6", "Sports & Outdoors", "Սպորտ և Հանգիստ", "Спорт и Отдых"),
]


def _seed_categories(apps, schema_editor) -> None:
    category_model = apps.get_model("metax", "CategoryModel")
    category_model.objects.bulk_create(
        [
            category_model(uuid=uuid_, name=name, name_hy=name_hy, name_ru=name_ru)
            for uuid_, name, name_hy, name_ru in _CATEGORIES
        ],
        # Idempotent: a re-run (or a partial previous run) skips rows already present.
        ignore_conflicts=True,
    )


def _unseed_categories(apps, schema_editor) -> None:
    category_model = apps.get_model("metax", "CategoryModel")
    category_model.objects.filter(uuid__in=[uuid_ for uuid_, *_ in _CATEGORIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("metax", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(_seed_categories, _unseed_categories),
    ]
