"""Seed example product names for the initial categories.

Each category is matched not only by its localized label but by these example product names, which
the embedding classifier turns into extra match anchors (a product named like an example snaps to
that category). Examples are stored newline-separated; add more any time via the Django admin on a
category (one per line or comma-separated) — that does not require a migration.

Keyed by the same hardcoded UUIDs as ``0002_seed_categories`` so this stays deterministic and
idempotent: re-applying just rewrites the same example text onto the same rows.
"""

from __future__ import annotations

from django.db import migrations

# Expanded example product names to act as stronger semantic anchors for the embedding classifier.
_EXAMPLES_BY_CATEGORY = {
    "019f006f-6337-7234-a483-53294ab7215e": [  # Groceries & Food
        "կաթ", "պանիր", "կարագ", "հաց", "ձու", "բրինձ", "մակարոն", "ալյուր",
        "շաքար", "աղ", "ձեթ", "մեղր", "թեյ", "սուրճ", "շոկոլադ", "երշիկ", "պաղպաղակ",
        "մածուն", "թթվասեր", "կաթնաշոռ", "հավի միս", "տավարի միս", "խոզի միս",
        "լոլիկ", "վարունգ", "կարտոֆիլ", "սոխ", "խնձոր", "բանան", "նարինջ",
        "ձուկ", "պահածո", "հավկիթ", "բաստուրմա", "սուջուխ", "լավաշ", "բուլկի",
    ],
    "019f006f-6337-7234-a483-532ae1279221": [  # Drinks & Alcohol
        "գարեջուր", "գինի", "օղի", "կոնյակ", "շամպայն", "հյութ", "ջուր",
        "լիմոնադ", "կոկա կոլա", "վիսկի", "էներգետիկ ըմպելիք", "ռոմ", "տեկիլա",
        "լիկյոր", "հանքային ջուր", "գազավորված ջուր", "թան", "կոմպոտ", "սառը թեյ",
    ],
    "019f006f-6337-7234-a483-532bacead220": [  # Electronics & Appliances
        "հեռախոս", "սմարթֆոն", "համակարգիչ", "նոութբուք", "հեռուստացույց",
        "լվացքի մեքենա", "սառնարան", "փոշեկուլ", "արդուկ", "միքսեր", "ականջակալ",
        "լիցքավորիչ", "պլանշետ", "էլեկտրական թեյնիկ", "օդորակիչ", "բլենդեր",
        "միկրոալիքային վառարան", "մանղալ", "սմարթ-ժամացույց", "մարտկոց", "power bank",
    ],
    "019f006f-6337-7234-a483-532c1117974f": [  # Clothing, Shoes & Fashion
        "վերնաշապիկ", "շապիկ", "տաբատ", "ջինս", "կոշիկ", "սպորտային կոշիկ",
        "բաճկոն", "վերարկու", "գուլպա", "գլխարկ", "զգեստ", "կուրտկա", "սվիտեր",
        "կիսաշրջազգեստ", "պիջակ", "ձեռնոց", "շարֆ", "գոտի", "պայուսակ", "դրամապանակ",
    ],
    "019f006f-6337-7234-a483-532df5e61e09": [  # Home & Garden
        "բազմոց", "բազկաթոռ", "սեղան", "աթոռ", "պահարան", "վարագույր",
        "բարձ", "սպասք", "ծաղկաման", "գորգ", "անկողին", "սավան", "վերմակ",
        "հայելի", "լամպ", "ջահ", "թավա", "կաթսա", "դանակ", "աղբաման",
    ],
    "019f006f-6337-7234-a483-532e26922575": [  # Health & Beauty
        "շամպուն", "օճառ", "կրեմ", "ատամի մածուկ", "ատամի խոզանակ",
        "օծանելիք", "դեզոդորանտ", "լոսյոն", "շրթներկ", "դիմակ", "մազերի ներկ",
        "դեղահաբ", "վիտամիններ", "սանիտայզեր", "խոնավ անձեռոցիկ", "լվացող գել",
    ],
    "019f006f-6337-7234-a483-532fff506c77": [  # Children & Baby Products
        "տակդիր", "մանկական խառնուրդ", "խաղալիք", "մանկասայլակ", "ծծակ",
        "մանկական հագուստ", "պամպերս", "մանկական կեր", "կրծկալ", "մանկական օճառ",
        "կառուսել", "խարխլատիչ", "լեգո",
    ],
    "019f006f-6337-7234-a483-53309db9ae74": [  # Pet Supplies
        "կատվի կեր", "շան կեր", "կատվի ավազ", "անասնակեր", "վանդակ",
        "վզկապ", "կենդանիների շամպուն", "խաղալիք կենդանիների համար", "տեղափոխման պայուսակ",
    ],
    "019f006f-6337-7234-a483-5331e4f969ca": [  # Automotive & Tools
        "մուրճ", "պտուտակ", "պտուտակիչ", "մեքենայի յուղ", "անվադող",
        "գործիքների հավաքածու", "մարտկոց", "ակոսահատ", "դանթել", "աքցան",
        "հակասառեցուցիչ", "անտիֆրիզ", "մեքենայի հոտավետիչ", "օտվյորտկա",
    ],
    "019f006f-6337-7234-a483-5332b813b6c7": [  # Stationery, Books & Hobbies
        "գիրք", "տետր", "գրիչ", "մատիտ", "մկրատ", "սոսինձ", "ալբոմ", "ներկ", "փազլ",
        "A4 թուղթ", "քանոն", "ֆլոմաստեր", "օրագիր", "կարկին", "սկոչ", "կավ",
    ],
    "019f006f-6337-7234-a483-53337b0550a6": [  # Sports & Outdoors
        "գնդակ", "ֆուտբոլի գնդակ", "հեծանիվ", "վրան", "քնապարկ", "դումբել",
        "յոգայի գորգ", "ուսապարկ", "սպորտային համազգեստ", "լողազգեստ", "ակնոց լողի",
        "ցատկապարան", "մարզասարք",
    ],
}


def _seed_examples(apps, schema_editor) -> None:
    category_model = apps.get_model("metax", "CategoryModel")
    for uuid_, examples in _EXAMPLES_BY_CATEGORY.items():
        category_model.objects.filter(uuid=uuid_).update(examples="\n".join(examples))


def _unseed_examples(apps, schema_editor) -> None:
    category_model = apps.get_model("metax", "CategoryModel")
    category_model.objects.filter(uuid__in=list(_EXAMPLES_BY_CATEGORY)).update(examples="")


class Migration(migrations.Migration):

    dependencies = [
        ("metax", "0002_seed_categories"),
    ]

    operations = [
        migrations.RunPython(_seed_examples, _unseed_examples),
    ]
