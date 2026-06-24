"""Seed the 7 product categories with names in English, Armenian, and Russian.

All three names are shown to the Ollama classifier in a single prompt line
(e.g. "Alcohol / Ալկոհոլ / Алкоголь") so the model can match product names
written in any of the three scripts without needing translation.
"""

from __future__ import annotations

import uuid

from django.db import migrations

_CATEGORIES = [
    {
        "name": "Alcohol",
        "name_hy": "Ալկոհոլ",
        "name_ru": "Алкоголь",
    },
    {
        "name": "Water & Juice",
        "name_hy": "Ջուր եւ հյութ",
        "name_ru": "Вода и соки",
    },
    {
        "name": "Dairy",
        "name_hy": "Կաթնամթերք",
        "name_ru": "Молочные продукты",
    },
    {
        "name": "Meat & Fish",
        "name_hy": "Միս եւ ձուկ",
        "name_ru": "Мясо и рыба",
    },
    {
        "name": "Sweets & Snacks",
        "name_hy": "Քաղցրեղեն եւ նախուտեստ",
        "name_ru": "Сладости и снеки",
    },
    {
        "name": "Coffee & Tea",
        "name_hy": "Սուրճ եւ թեյ",
        "name_ru": "Кофе и чай",
    },
    {
        "name": "Personal Care",
        "name_hy": "Անձնական խնամք",
        "name_ru": "Личная гигиена",
    },
]

_CATEGORY_NAMES = [c["name"] for c in _CATEGORIES]


def _seed(apps, schema_editor):
    Category = apps.get_model("metax", "CategoryModel")
    for cat in _CATEGORIES:
        Category.objects.get_or_create(
            name=cat["name"],
            defaults={
                "uuid": uuid.uuid7(),
                "name_hy": cat["name_hy"],
                "name_ru": cat["name_ru"],
            },
        )


def _unseed(apps, schema_editor):
    apps.get_model("metax", "CategoryModel").objects.filter(name__in=_CATEGORY_NAMES).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("metax", "0006_add_category_multilingual_names"),
    ]

    operations = [
        migrations.RunPython(_seed, _unseed),
    ]
