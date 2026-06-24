"""Data migration: seed initial categories and their helper words.

Categories are intentionally broad and few (7) to keep the bot UI clean.
Helper words use three scripts — Armenian (հայ), Russian (рус), English — so
the substring classifier catches product names from both Yerevan City and SAS AM.
"""

from __future__ import annotations

import uuid

from django.db import migrations

# ---------------------------------------------------------------------------
# Seed data
# Each entry: {"name": str, "helper_words": list[str]}
# Helper-word text is globally unique (DB constraint), so words must not
# appear in more than one category.
# ---------------------------------------------------------------------------

_CATEGORIES: list[dict] = [
    {
        "name": "Alcohol",
        "helper_words": [
            # Armenian
            "գինի",        # wine
            # Russian
            "вино", "водка", "коньяк", "пиво", "виски",
            "шампанское", "бренди", "ликёр", "ром", "текила",
            # English
            "wine", "vodka", "beer", "whiskey", "cognac",
            "brandy", "champagne", "cider",
        ],
    },
    {
        "name": "Water & Juice",
        "helper_words": [
            # Armenian
            "ջուր",        # water
            "հյութ",       # juice
            # Russian
            "вода", "сок", "нектар", "лимонад", "минеральн",
            # English
            "water", "juice",
        ],
    },
    {
        "name": "Dairy",
        "helper_words": [
            # Russian
            "молоко", "молочн", "сыр", "йогурт", "кефир",
            "сметан", "творог", "ряженк", "сливочн",
            # English
            "milk", "cheese", "yogurt", "kefir", "butter",
        ],
    },
    {
        "name": "Meat & Fish",
        "helper_words": [
            # Russian
            "мясо", "рыба", "курица", "говядин", "свинин",
            "колбас", "сосиск", "фарш", "лосось", "тунец",
            "форель", "семга", "креветк",
            # English
            "chicken", "beef", "pork", "fish", "salmon",
            "shrimp", "turkey", "sausage", "meat", "tuna",
        ],
    },
    {
        "name": "Sweets & Snacks",
        "helper_words": [
            # Russian
            "шоколад", "конфет", "печенье", "торт", "вафл",
            "чипсы", "зефир", "мармелад", "пряник", "халва", "бисквит",
            # English
            "chocolate", "candy", "chip", "cookie", "cake",
            "waffle", "snack",
        ],
    },
    {
        "name": "Coffee & Tea",
        "helper_words": [
            # Russian
            "кофе", "чай", "какао",
            # English
            "coffee", "tea", "cocoa",
        ],
    },
    {
        "name": "Personal Care",
        "helper_words": [
            # Russian
            "шампунь", "зубн", "дезодор", "духи",
            "гель для душа", "помада", "тушь",
            # English
            "shampoo", "toothpaste", "deodorant",
            "perfume", "lotion",
        ],
    },
]

_CATEGORY_NAMES = [c["name"] for c in _CATEGORIES]


def _seed(apps, schema_editor):
    Category = apps.get_model("metax", "CategoryModel")
    HelperWord = apps.get_model("metax", "CategoryHelperWordsModel")

    for cat_data in _CATEGORIES:
        category, _ = Category.objects.get_or_create(
            name=cat_data["name"],
            defaults={"uuid": uuid.uuid7()},
        )
        for word in cat_data["helper_words"]:
            HelperWord.objects.get_or_create(
                helper_word_text=word,
                defaults={
                    "uuid": uuid.uuid7(),
                    "category": category,
                },
            )


def _unseed(apps, schema_editor):
    Category = apps.get_model("metax", "CategoryModel")
    # Helper words are deleted via CASCADE when the category is deleted.
    Category.objects.filter(name__in=_CATEGORY_NAMES).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("metax", "0002_add_image_url_2026_06_01_0000"),
    ]

    operations = [
        migrations.RunPython(_seed, _unseed),
    ]
