"""Telegram bot texts, language helpers and display names (pure, stateless)."""

from __future__ import annotations

from aiogram.types import BotCommand

SUPPORTED_LANGUAGES = ("hy", "ru", "en")
DEFAULT_LANGUAGE = "en"

# Pretty display labels for known retailers; unknown ones fall back to a title-cased name.
_RETAILER_DISPLAY_NAMES: dict[str, str] = {
    "sas-am": "SAS",
    "yerevan-city": "Yerevan City",
    "rouge-am": "ROUGE",
    "tntesakan-am": "Tntesakan.am",
    "vlv-am": "VLV",
    "zigzag-am": "ZigZag",
}

_TEXTS: dict[str, dict[str, str]] = {
    "en": {
        "choose_language": "Choose your language:",
        "intro": (
            "<b>Metax Bot</b> 🛒\n\n"
            "Browse today's actual discounts in popular Armenian supermarkets.\n\n"
            "Main feature: search. Type a product name and I will return matching products with images and pagination.\n\n"
            "You can also narrow results by retailer whenever you want."
        ),
        "help": (
            "<b>Metax Bot</b>\n\n"
            "Type a product name to search discounts. Results are shown with images and pagination.\n\n"
            "You can also filter results by retailer."
        ),
        "search_prompt": "Send a product name to search discounts.",
        "search_example": "Example: <code>milk</code>",
        "search_loading": "🔍 Searching...",
        "search_error": "⚠️ Search failed. Please try again later.",
        "search_empty": "🔍 <b>«{query}»</b> — found: 0\n\nNothing matched this query.",
        "search_empty_filtered": (
            "🔍 <b>«{query}»</b> · 🏪 {retailer} — found: 0\n\n"
            "Nothing matched in <b>{retailer}</b>. The retailer filter is on — "
            "tap «Show all retailers» to search every store."
        ),
        "category_empty_filtered": (
            "📂 No products from <b>{retailer}</b> in this category yet.\n\n"
            "The retailer filter is on — tap «Show all retailers» to see every store."
        ),
        "results_found": "found",
        "page": "page",
        "back": "← Back",
        "next": "Next →",
        "clear_retailer_filter": "Show all retailers",
        "choose_retailer": "Choose a retailer:",
        "retailer_filter_hint": "Narrow results to one store or browse all stores.",
        "current_filter": "Search in",
        "current_filter_none": "all stores",
        "categories_title": "📂 Choose a category:",
        "categories_none": "No categories yet.",
        "category_empty": "📂 No products in this category yet.",
        "browse_categories": "📂 Categories",
        "browse_stores": "🏪 Stores",
        "stores_title": "🏪 Choose a store to see its discounts:",
        "stores_none": "No stores yet.",
        "store_empty": "🏪 <b>{retailer}</b> has no discounts right now.",
        "search_in_store": "🔍 Search in {retailer}",
        "store_search_prompt": "🔍 Type a product name — I'll search only in <b>{retailer}</b>.",
        "unsupported": "Send a product name to search discounts.",
        "throttle": "⏳ Too fast. Please wait a second.",
        "image_unavailable": "🚫 <i>Image unavailable</i>",
        "open_link": "Open →",
    },
    "ru": {
        "choose_language": "Выберите язык:",
        "intro": (
            "<b>Metax Bot</b> 🛒\n\n"
            "Смотрите актуальные скидки сегодняшнего дня в популярных армянских супермаркетах.\n\n"
            "Главная функция — поиск. Просто напишите название товара, и бот покажет совпадения с изображениями и пагинацией.\n\n"
            "При желании можно сузить результаты по магазину."
        ),
        "help": (
            "<b>Metax Bot</b>\n\n"
            "Напишите название товара, чтобы найти скидки. Результаты показываются с изображениями и пагинацией.\n\n"
            "Также можно фильтровать результаты по магазину."
        ),
        "search_prompt": "Напишите название товара для поиска скидок.",
        "search_example": "Пример: <code>молоко</code>",
        "search_loading": "🔍 Ищу...",
        "search_error": "⚠️ Ошибка при поиске. Попробуйте позже.",
        "search_empty": "🔍 <b>«{query}»</b> — найдено: 0\n\nПо этому запросу ничего не найдено.",
        "search_empty_filtered": (
            "🔍 <b>«{query}»</b> · 🏪 {retailer} — найдено: 0\n\n"
            "В магазине <b>{retailer}</b> ничего не найдено. Включён фильтр по магазину — "
            "нажмите «Показать все магазины», чтобы искать везде."
        ),
        "category_empty_filtered": (
            "📂 В этой категории пока нет товаров из <b>{retailer}</b>.\n\n"
            "Включён фильтр по магазину — нажмите «Показать все магазины», чтобы увидеть все."
        ),
        "results_found": "найдено",
        "page": "стр.",
        "back": "← Назад",
        "next": "Далее →",
        "clear_retailer_filter": "Показать все магазины",
        "choose_retailer": "Выберите магазин:",
        "retailer_filter_hint": "Сузьте результаты до одного магазина или смотрите все сразу.",
        "current_filter": "Искать в",
        "current_filter_none": "все магазины",
        "categories_title": "📂 Выберите категорию:",
        "categories_none": "Категорий пока нет.",
        "category_empty": "📂 В этой категории пока нет товаров.",
        "browse_categories": "📂 Категории",
        "browse_stores": "🏪 Магазины",
        "stores_title": "🏪 Выберите магазин, чтобы увидеть его скидки:",
        "stores_none": "Магазинов пока нет.",
        "store_empty": "🏪 В <b>{retailer}</b> сейчас нет скидок.",
        "search_in_store": "🔍 Искать в {retailer}",
        "store_search_prompt": "🔍 Напишите название товара — буду искать только в <b>{retailer}</b>.",
        "unsupported": "Напишите название товара для поиска скидок.",
        "throttle": "⏳ Слишком быстро. Подождите секунду.",
        "image_unavailable": "🚫 <i>Изображение недоступно</i>",
        "open_link": "Открыть →",
    },
    "hy": {
        "choose_language": "Ընտրեք լեզուն՝",
        "intro": (
            "<b>Metax Bot</b> 🛒\n\n"
            "Դիտեք այսօրվա իրական զեղչերը հայտնի հայկական սուպերմարկետներում։\n\n"
            "Հիմնական գործառույթը որոնումն է. պարզապես գրեք ապրանքի անունը, և բոտը կվերադարձնի համապատասխան ապրանքները՝ պատկերներով և էջավորմամբ։\n\n"
            "Ցանկության դեպքում կարող եք նաև նեղացնել արդյունքները ըստ խանութի։"
        ),
        "help": (
            "<b>Metax Bot</b>\n\n"
            "Գրեք ապրանքի անունը՝ զեղչերը գտնելու համար։ Արդյունքները ցույց են տրվում պատկերներով և էջավորմամբ։\n\n"
            "Կարող եք նաև ֆիլտրել արդյունքները ըստ խանութի։"
        ),
        "search_prompt": "Գրեք ապրանքի անունը՝ զեղչերը որոնելու համար։",
        "search_example": "Օրինակ՝ <code>կաթ</code>",
        "search_loading": "🔍 Որոնում եմ...",
        "search_error": "⚠️ Որոնման ժամանակ սխալ առաջացավ։ Խնդրում ենք փորձել ավելի ուշ։",
        "search_empty": "🔍 <b>«{query}»</b> — գտնվել է՝ 0\n\nԱյս հարցման համար ոչինչ չի գտնվել։",
        "search_empty_filtered": (
            "🔍 <b>«{query}»</b> · 🏪 {retailer} — գտնվել է՝ 0\n\n"
            "<b>{retailer}</b> խանութում ոչինչ չի գտնվել։ Միացված է խանութի ֆիլտրը — "
            "սեղմեք «Ցուցադրել բոլոր խանութները»՝ բոլոր խանութներում որոնելու համար։"
        ),
        "category_empty_filtered": (
            "📂 Այս կատեգորիայում դեռ չկան <b>{retailer}</b> խանութի ապրանքներ։\n\n"
            "Միացված է խանութի ֆիլտրը — սեղմեք «Ցուցադրել բոլոր խանութները»՝ բոլորը տեսնելու համար։"
        ),
        "results_found": "գտնվել է",
        "page": "էջ",
        "back": "← Հետ",
        "next": "Հաջորդ →",
        "clear_retailer_filter": "Ցուցադրել բոլոր խանութները",
        "choose_retailer": "Ընտրեք խանութը՝",
        "retailer_filter_hint": "Նեղացրեք արդյունքները մեկ խանութով կամ դիտեք բոլորը։",
        "current_filter": "Որոնել",
        "current_filter_none": "բոլոր խանութներում",
        "categories_title": "📂 Ընտրեք կատեգորիան՝",
        "categories_none": "Կատեգորիաներ դեռ չկան։",
        "category_empty": "📂 Այս կատեգորիայում դեռ ապրանքներ չկան։",
        "browse_categories": "📂 Կատեգորիաներ",
        "browse_stores": "🏪 Խանութներ",
        "stores_title": "🏪 Ընտրեք խանութը՝ նրա զեղչերը տեսնելու համար՝",
        "stores_none": "Խանութներ դեռ չկան։",
        "store_empty": "🏪 <b>{retailer}</b> խանութում այս պահին զեղչեր չկան։",
        "search_in_store": "🔍 Որոնել {retailer}-ում",
        "store_search_prompt": "🔍 Գրեք ապրանքի անունը — կորոնեմ միայն <b>{retailer}</b> խանութում։",
        "unsupported": "Գրեք ապրանքի անունը՝ զեղչերը որոնելու համար։",
        "throttle": "⏳ Շատ արագ է։ Խնդրում ենք սպասել մեկ վայրկյան։",
        "image_unavailable": "🚫 <i>Նկարը հասանելի չէ</i>",
        "open_link": "Բացել →",
    },
}

_LANGUAGE_BUTTONS: dict[str, str] = {
    "hy": "Հայերեն",
    "ru": "Русский",
    "en": "English",
}


def normalize_language(language_code: str | None) -> str:
    if language_code in SUPPORTED_LANGUAGES:
        return language_code
    return DEFAULT_LANGUAGE


def retailer_display_name(name: str) -> str:
    """Map an internal retailer name to a user-facing label.

    Returns:
        A pretty display label for known retailers, else a title-cased fallback.
    """
    return _RETAILER_DISPLAY_NAMES.get(name, name.replace("-", " ").replace("_", " ").title())


def localized_category_name(name: str, name_hy: str, name_ru: str, language_code: str) -> str:
    """Pick a category's name in the user's language, falling back to the English ``name``.

    Returns:
        The localized name when available, otherwise the English ``name``.
    """
    localized = {"hy": name_hy, "ru": name_ru}.get(normalize_language(language_code), "")
    return localized or name


def t(language_code: str, key: str, **kwargs: str) -> str:
    language = normalize_language(language_code)
    template = _TEXTS[language][key]
    return template.format(**kwargs)


def language_buttons() -> list[tuple[str, str]]:
    return [(label, code) for code, label in _LANGUAGE_BUTTONS.items()]


def bot_commands_for_language(language_code: str) -> list[BotCommand]:
    language = normalize_language(language_code)
    return [
        BotCommand(
            command="start", description={"hy": "Սկսել", "ru": "Запустить бота", "en": "Start bot"}[language]
        ),
        BotCommand(
            command="search",
            description={
                "hy": "Որոնել ապրանքներ",
                "ru": "Поиск товаров со скидками",
                "en": "Search discounted products",
            }[language],
        ),
        BotCommand(
            command="categories",
            description={
                "hy": "Դիտել ըստ կատեգորիայի",
                "ru": "Смотреть по категориям",
                "en": "Browse by category",
            }[language],
        ),
        BotCommand(
            command="stores",
            description={
                "hy": "Դիտել խանութի զեղչերը",
                "ru": "Скидки по магазинам",
                "en": "Browse a store's discounts",
            }[language],
        ),
        BotCommand(command="help", description={"hy": "Օգնություն", "ru": "Справка", "en": "Help"}[language]),
    ]
