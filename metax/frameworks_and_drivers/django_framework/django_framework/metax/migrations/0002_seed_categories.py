"""Seed the product categories (with example anchors) used for auto-categorization.

Categories are reference data: the embedding classifier loads them at crawl time and can only assign
a product to a category that exists (it no-ops when there are none). Each row carries
English/Armenian/Russian names so the classifier can embed all three localized labels, plus example
product names that act as stronger semantic anchors (a product named like an example snaps to that
category). Examples are stored newline-separated; add more any time via the Django admin — that does
not require a migration.

Only categories are seeded here. Retailers are *business* data, not reference data — they are created
and configured (including each one's optional fixed ``default_category``) from the Django admin, so
none are hardcoded in a migration.

All UUIDs are hardcoded (and are valid version-7 UUIDs, which the domain entities require on load) so
the migration is deterministic and idempotent: re-applying inserts nothing new and existing products
keep pointing at the same category rows. ``created_at``/``updated_at`` are left to their DB defaults
(``Now()``).
"""

from __future__ import annotations

from django.db import migrations

# (uuid, name, name_hy, name_ru, [example product names])
# The examples act as extra semantic anchors for the embedding classifier.
_CATEGORIES = [
    (
        "019f006f-6337-7234-a483-53294ab7215e",
        "Groceries & Food",
        "Սննդամթերք",
        "Продукты питания",
        [
            "կաթ", "պանիր", "կարագ", "հաց", "ձու", "բրինձ", "մակարոն", "ալյուր",
            "շաքար", "աղ", "ձեթ", "մեղր", "թեյ", "սուրճ", "շոկոլադ", "երշիկ", "պաղպաղակ",
            "մածուն", "թթվասեր", "կաթնաշոռ", "հավի միս", "տավարի միս", "խոզի միս",
            "լոլիկ", "վարունգ", "կարտոֆիլ", "սոխ", "խնձոր", "բանան", "նարինջ",
            "ձուկ", "պահածո", "հավկիթ", "բաստուրմա", "սուջուխ", "լավաշ", "բուլկի",
        ],
    ),
    (
        "019f006f-6337-7234-a483-532ae1279221",
        "Drinks & Alcohol",
        "Ըմպելիքներ և Ալկոհոլ",
        "Напитки и Алкоголь",
        [
            "գարեջուր", "գինի", "օղի", "կոնյակ", "շամպայն", "հյութ", "ջուր",
            "լիմոնադ", "կոկա կոլա", "վիսկի", "էներգետիկ ըմպելիք", "ռոմ", "տեկիլա",
            "լիկյոր", "հանքային ջուր", "գազավորված ջուր", "թան", "կոմպոտ", "սառը թեյ",
        ],
    ),
    (
        "019f006f-6337-7234-a483-532bacead220",
        "Electronics & Appliances",
        "Էլեկտրոնիկա և Կենցաղային տեխնիկա",
        "Электроника и Техника",
        [
            "հեռախոս", "սմարթֆոն", "համակարգիչ", "նոութբուք", "հեռուստացույց",
            "լվացքի մեքենա", "սառնարան", "փոշեկուլ", "արդուկ", "միքսեր", "ականջակալ",
            "լիցքավորիչ", "պլանշետ", "էլեկտրական թեյնիկ", "օդորակիչ", "բլենդեր",
            "միկրոալիքային վառարան", "մանղալ", "սմարթ-ժամացույց", "մարտկոց", "power bank",
        ],
    ),
    (
        "019f006f-6337-7234-a483-532c1117974f",
        "Clothing, Shoes & Fashion",
        "Հագուստ և Կոշիկ",
        "Одежда, Обувь и Мода",
        [
            "վերնաշապիկ", "շապիկ", "տաբատ", "ջինս", "կոշիկ", "սպորտային կոշիկ",
            "բաճկոն", "վերարկու", "գուլպա", "գլխարկ", "զգեստ", "կուրտկա", "սվիտեր",
            "կիսաշրջազգեստ", "պիջակ", "ձեռնոց", "շարֆ", "գոտի", "պայուսակ", "դրամապանակ",
        ],
    ),
    (
        "019f006f-6337-7234-a483-532df5e61e09",
        "Household goods",
        "Տնտեսական ապրանքներ",
        "Хозяйственные товары",
        [
            "բազմոց", "բազկաթոռ", "սեղան", "աթոռ", "պահարան", "վարագույր",
            "բարձ", "սպասք", "ծաղկաման", "գորգ", "անկողին", "սավան", "վերմակ",
            "հայելի", "լամպ", "ջահ", "թավա", "կաթսա", "դանակ", "աղբաման",
        ],
    ),
    (
        "019f006f-6337-7234-a483-532e26922575",
        "Health & Beauty",
        "Գեղեցկություն և խնամք",
        "Здоровье и Красота",
        [
            "շամպուն", "օճառ", "կրեմ", "ատամի մածուկ", "ատամի խոզանակ",
            "օծանելիք", "դեզոդորանտ", "լոսյոն", "շրթներկ", "դիմակ", "մազերի ներկ",
            "դեղահաբ", "վիտամիններ", "սանիտայզեր", "խոնավ անձեռոցիկ", "լվացող գել",
        ],
    ),
    (
        "019f006f-6337-7234-a483-532fff506c77",
        "Children & Baby Products",
        "Մանկական ապրանքներ",
        "Детские товары",
        [
            "տակդիր", "մանկական խառնուրդ", "խաղալիք", "մանկասայլակ", "ծծակ",
            "մանկական հագուստ", "պամպերս", "մանկական կեր", "կրծկալ", "մանկական օճառ",
            "կառուսել", "խարխլատիչ", "լեգո",
        ],
    ),
    (
        "019f006f-6337-7234-a483-53309db9ae74",
        "Pet Supplies",
        "Կենդանիների խնամք",
        "Товары для животных",
        [
            "կատվի կեր", "շան կեր", "կատվի ավազ", "անասնակեր", "վանդակ",
            "վզկապ", "կենդանիների շամպուն", "խաղալիք կենդանիների համար", "տեղափոխման պայուսակ",
        ],
    ),
    (
        "019f006f-6337-7234-a483-5331e4f969ca",
        "Automotive & Tools",
        "Գործիքներ և Ավտոապրանքներ",
        "Автотовары и Инструменты",
        [
            "մուրճ", "պտուտակ", "պտուտակիչ", "մեքենայի յուղ", "անվադող",
            "գործիքների հավաքածու", "մարտկոց", "ակոսահատ", "դանթել", "աքցան",
            "հակասառեցուցիչ", "անտիֆրիզ", "մեքենայի հոտավետիչ", "օտվյորտկա",
        ],
    ),
    (
        "019f006f-6337-7234-a483-5332b813b6c7",
        "Stationery, Books",
        "Գրենական պիտույքներ, Գրքեր",
        "Канцтовары и Книги",
        [
            "գիրք", "տետր", "գրիչ", "մատիտ", "մկրատ", "սոսինձ", "ալբոմ", "ներկ", "փազլ",
            "A4 թուղթ", "քանոն", "ֆլոմաստեր", "օրագիր", "կարկին", "սկոչ", "կավ",
        ],
    ),
    (
        "019f006f-6337-7234-a483-53337b0550a6",
        "Sports & Outdoors",
        "Սպորտ և Հանգիստ",
        "Спорт и Отдых",
        [
            "գնդակ", "ֆուտբոլի գնդակ", "հեծանիվ", "վրան", "քնապարկ", "դումբել",
            "յոգայի գորգ", "ուսապարկ", "սպորտային համազգեստ", "լողազգեստ", "ակնոց լողի",
            "ցատկապարան", "մարզասարք",
        ],
    ),
]


def _seed_categories(apps, schema_editor) -> None:
    category_model = apps.get_model("metax", "CategoryModel")
    category_model.objects.bulk_create(
        [
            category_model(
                uuid=uuid_, name=name, name_hy=name_hy, name_ru=name_ru, examples="\n".join(examples)
            )
            for uuid_, name, name_hy, name_ru, examples in _CATEGORIES
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
