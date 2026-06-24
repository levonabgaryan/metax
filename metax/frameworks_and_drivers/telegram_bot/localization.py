"""Telegram bot text and language preference helpers."""

from __future__ import annotations

from aiogram.types import BotCommand

SUPPORTED_LANGUAGES = ("hy", "ru", "en")
DEFAULT_LANGUAGE = "en"

_USER_LANGUAGES: dict[int, str] = {}
_USER_RETAILER_FILTERS: dict[int, str | None] = {}
# Last search query per user, so changing the retailer filter can re-run it.
_USER_LAST_QUERIES: dict[int, str] = {}

# Pretty display labels for known retailers; unknown ones fall back to a title-cased name.
_RETAILER_DISPLAY_NAMES: dict[str, str] = {
    "sas-am": "SAS",
    "yerevan-city": "Yerevan City",
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
        "results_found": "found",
        "page": "page",
        "back": "← Back",
        "next": "Next →",
        "filter_by_retailer": "Filter by retailer",
        "clear_retailer_filter": "Show all retailers",
        "choose_retailer": "Choose a retailer:",
        "retailer_filter_hint": "Narrow results to one store or browse all stores.",
        "retailer_filter_set": "Retailer filter: {retailer_name}",
        "retailer_filter_cleared": "Retailer filter cleared.",
        "current_filter": "Retailer filter",
        "current_filter_none": "All retailers",
        "categories_disabled": "📂 Categories are disabled for now.",
        "unsupported": "Send a product name to search discounts.",
        "throttle": "⏳ Too fast. Please wait a second.",
        "image_unavailable": "🚫 <i>Image unavailable</i>",
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
        "results_found": "найдено",
        "page": "стр.",
        "back": "← Назад",
        "next": "Далее →",
        "filter_by_retailer": "Фильтр по магазину",
        "clear_retailer_filter": "Показать все магазины",
        "choose_retailer": "Выберите магазин:",
        "retailer_filter_hint": "Сузьте результаты до одного магазина или смотрите все сразу.",
        "retailer_filter_set": "Фильтр по магазину: {retailer_name}",
        "retailer_filter_cleared": "Фильтр по магазину отключен.",
        "current_filter": "Фильтр",
        "current_filter_none": "Все магазины",
        "categories_disabled": "📂 Категории сейчас отключены.",
        "unsupported": "Напишите название товара для поиска скидок.",
        "throttle": "⏳ Слишком быстро. Подождите секунду.",
        "image_unavailable": "🚫 <i>Изображение недоступно</i>",
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
        "results_found": "գտնվել է",
        "page": "էջ",
        "back": "← Հետ",
        "next": "Հաջորդ →",
        "filter_by_retailer": "Ֆիլտրել ըստ խանութի",
        "clear_retailer_filter": "Ցուցադրել բոլոր խանութները",
        "choose_retailer": "Ընտրեք խանութը՝",
        "retailer_filter_hint": "Նեղացրեք արդյունքները մեկ խանութով կամ դիտեք բոլորը։",
        "retailer_filter_set": "Խանութի ֆիլտր՝ {retailer_name}",
        "retailer_filter_cleared": "Խանութի ֆիլտրը հանված է։",
        "current_filter": "Ֆիլտր",
        "current_filter_none": "Բոլոր խանութները",
        "categories_disabled": "📂 Կատեգորիաները ժամանակավորապես անջատված են։",
        "unsupported": "Գրեք ապրանքի անունը՝ զեղչերը որոնելու համար։",
        "throttle": "⏳ Շատ արագ է։ Խնդրում ենք սպասել մեկ վայրկյան։",
        "image_unavailable": "🚫 <i>Նկարը հասանելի չէ</i>",
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


def set_user_language(user_id: int, language_code: str) -> None:
    _USER_LANGUAGES[user_id] = normalize_language(language_code)


def get_user_language(user_id: int | None) -> str:
    if user_id is None:
        return DEFAULT_LANGUAGE
    return normalize_language(_USER_LANGUAGES.get(user_id))


def set_user_retailer_filter(user_id: int, retailer_uuid: str | None) -> None:
    _USER_RETAILER_FILTERS[user_id] = retailer_uuid


def get_user_retailer_filter(user_id: int | None) -> str | None:
    if user_id is None:
        return None
    return _USER_RETAILER_FILTERS.get(user_id)


def set_user_last_query(user_id: int, query: str) -> None:
    _USER_LAST_QUERIES[user_id] = query


def get_user_last_query(user_id: int | None) -> str | None:
    if user_id is None:
        return None
    return _USER_LAST_QUERIES.get(user_id)


def retailer_display_name(name: str) -> str:
    """Map an internal retailer name to a user-facing label.

    Returns:
        A pretty display label for known retailers, else a title-cased fallback.
    """
    return _RETAILER_DISPLAY_NAMES.get(name, name.replace("-", " ").replace("_", " ").title())


def t(language_code: str, key: str, **kwargs: str) -> str:
    language = normalize_language(language_code)
    template = _TEXTS[language][key]
    return template.format(**kwargs)


def language_buttons() -> list[tuple[str, str]]:
    return [(label, code) for code, label in _LANGUAGE_BUTTONS.items()]


def bot_commands_for_language(language_code: str) -> list[BotCommand]:
    language = normalize_language(language_code)
    return [
        BotCommand(command="start", description={"hy": "Սկսել", "ru": "Запустить бота", "en": "Start bot"}[language]),
        BotCommand(
            command="search",
            description={
                "hy": "Որոնել ապրանքներ",
                "ru": "Поиск товаров со скидками",
                "en": "Search discounted products",
            }[language],
        ),
        BotCommand(command="help", description={"hy": "Օգնություն", "ru": "Справка", "en": "Help"}[language]),
    ]
