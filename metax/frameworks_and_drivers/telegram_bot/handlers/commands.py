"""Command handlers: /start, /help, /search, /categories."""

from __future__ import annotations

import asyncio
import html
import logging
import re
from pathlib import Path
from urllib.parse import quote, urlsplit
from uuid import UUID

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    BufferedInputFile,
    InlineKeyboardMarkup,
    InputFile,
    InputMediaPhoto,
    LinkPreviewOptions,
    Message,
)
from aiogram.types.media_union import MediaUnion

from metax.core.application.read_models.discounted_product import DiscountedProductReadModel
from metax.frameworks_and_drivers.telegram_bot.formatters import format_product
from metax.frameworks_and_drivers.telegram_bot.keyboards import (
    PAGE_SIZE,
    categories_keyboard,
    clamp_query,
    language_keyboard,
    search_result_keyboard,
)
from metax.frameworks_and_drivers.telegram_bot.localization import (
    get_user_language,
    get_user_retailer_filter,
    localized_category_name,
    set_user_last_query,
    t,
)
from metax_bootstrap import METAX_LIFESPAN_MANAGER

logger = logging.getLogger(__name__)

router = Router()

_LINK_PREVIEW_DISABLED = LinkPreviewOptions(is_disabled=True)

# Telegram hard limit on items per sendMediaGroup call.
_MEDIA_GROUP_MAX = 10


# Static placeholder shown in place of an image Telegram cannot fetch, so the album stays whole.
_PLACEHOLDER_BYTES = (Path(__file__).resolve().parent.parent / "assets" / "no_image.png").read_bytes()

# Telegram reports a rejected album item as "...failed to send message #N..." (1-based).
_FAILED_ITEM_RE = re.compile(r"message #(\d+)")

# Hosts whose images Telegram's own fetcher cannot reliably retrieve. tntesakan.am publishes a
# dead IPv6 (AAAA) record and sits on slow reg.ru shared hosting, so Telegram's short-timeout,
# IPv6-preferring fetch times out and the album degrades to placeholders. We can't change their
# hosting, so we hand Telegram a cached CDN mirror (images.weserv.nl, on Cloudflare — healthy
# IPv6, fast edges) instead. This is a pure URL rewrite: no image bytes ever touch our server;
# the CDN fetches and caches the origin over IPv4 itself.
_TELEGRAM_UNFETCHABLE_IMAGE_HOSTS = frozenset({"tntesakan.am", "www.tntesakan.am"})


def _telegram_fetchable_url(image_url: str) -> str:
    """Return a URL Telegram can fetch, routing known-unfetchable hosts through an image CDN."""
    host = (urlsplit(image_url).hostname or "").lower()
    if host not in _TELEGRAM_UNFETCHABLE_IMAGE_HOSTS:
        return image_url
    # weserv takes the source without its scheme; the ssl: prefix forces an HTTPS origin fetch and
    # output=jpg normalises every format (incl. tntesakan's webp) to a Telegram-safe JPEG.
    source = image_url.split("://", 1)[-1]
    return "https://images.weserv.nl/?url=" + quote(f"ssl:{source}", safe="") + "&output=jpg"


def _photo_media(ref: str | InputFile, caption: str) -> MediaUnion:
    return InputMediaPhoto(media=ref, caption=caption, parse_mode=ParseMode.HTML)


def _placeholder_media(caption: str, note: str) -> MediaUnion:
    return _photo_media(
        BufferedInputFile(_PLACEHOLDER_BYTES, filename="no_image.png"),
        f"{note}\n{caption}",
    )


def _failed_media_index(message: str, count: int) -> int | None:
    """Parse the 0-based index of the album item Telegram rejected.

    Returns:
        The item index, or ``None`` if Telegram did not name one (and it is not a single send).
    """
    match = _FAILED_ITEM_RE.search(message)
    if match:
        index = int(match.group(1)) - 1
        if 0 <= index < count:
            return index
    # A single-photo send has no item number, so the lone item is the culprit.
    return 0 if count == 1 else None


async def _deliver(reply_target: Message, media: list[MediaUnion]) -> None:
    if len(media) == 1:
        only = media[0]
        await reply_target.answer_photo(
            photo=only.media, caption=only.caption, parse_mode=ParseMode.HTML
        )
    else:
        await reply_target.answer_media_group(media=media)


async def _send_album_or_photo(reply_target: Message, media: list[MediaUnion]) -> None:
    """Send media as an album (2+ items) or a single photo, retrying once on flood control (429)."""
    try:
        await _deliver(reply_target, media)
    except TelegramRetryAfter as err:
        await asyncio.sleep(err.retry_after)
        await _deliver(reply_target, media)


async def _send_photo_group(
    reply_target: Message, items: list[tuple[str, str]], image_unavailable: str
) -> None:
    """Send up to 10 ``(image_url, caption)`` items as a single album.

    Telegram fetches the URLs itself. If it rejects one (too large or unfetchable) it names the
    offending item, so we swap that slot for a static placeholder — captioned with
    ``image_unavailable`` — and re-send, keeping the album whole instead of degrading to
    one-by-one.
    """
    if not items:
        return

    media = [_photo_media(url, caption) for url, caption in items]
    for _attempt in range(len(media) + 1):
        try:
            await _send_album_or_photo(reply_target, media)
            return
        except TelegramBadRequest as err:
            index = _failed_media_index(err.message, len(media))
            if index is None:
                logger.warning("Album send failed; could not identify the bad image (%s)", err.message)
                break
            url, caption = items[index]
            logger.warning("Image unfetchable, using placeholder | url=%r", url)
            media[index] = _placeholder_media(caption, image_unavailable)

    # Safety net: if the album still cannot be sent, fall back to text so nothing is lost.
    for _url, caption in items:
        await reply_target.answer(
            caption, parse_mode=ParseMode.HTML, link_preview_options=_LINK_PREVIEW_DISABLED
        )


async def send_product_page(
    reply_target: Message,
    products: list[DiscountedProductReadModel],
    total: int,
    offset: int,
    header: str,
    summary_label: str,
    page_label: str,
    image_unavailable: str,
    keyboard: InlineKeyboardMarkup | None,
    language_code: str,
) -> None:
    # Group all photos into a single album (one API call) instead of one send per
    # product — cuts Telegram API calls ~5x and eases per-chat/global flood limits.
    items: list[tuple[str, str]] = []
    text_only: list[str] = []
    for n, p in enumerate(products, start=offset + 1):
        text = format_product(p, n, language_code)
        image_url = p.get("image_url")
        if image_url and image_url.startswith(("http://", "https://")):
            items.append((_telegram_fetchable_url(image_url), text))
        else:
            text_only.append(text)

    for start in range(0, len(items), _MEDIA_GROUP_MAX):
        await _send_photo_group(reply_target, items[start : start + _MEDIA_GROUP_MAX], image_unavailable)

    for text in text_only:
        await reply_target.answer(
            text,
            parse_mode=ParseMode.HTML,
            link_preview_options=_LINK_PREVIEW_DISABLED,
        )

    page = offset // PAGE_SIZE + 1
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    await reply_target.answer(
        f"{header} — {summary_label}: {total} • {page_label} {page}/{total_pages}",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
        link_preview_options=_LINK_PREVIEW_DISABLED,
    )


async def run_search(message: Message, raw_query: str) -> None:
    lang = get_user_language(message.from_user.id if message.from_user else None)
    retailer_uuid = get_user_retailer_filter(message.from_user.id if message.from_user else None)
    selected_retailer_name: str | None = None
    display_query = raw_query.strip()
    if not display_query:
        await message.answer(
            f"{t(lang, 'search_prompt')}\n{t(lang, 'search_example')}",
            parse_mode=ParseMode.HTML,
        )
        return

    search_query = clamp_query(display_query)
    if message.from_user:
        # Remember the query so changing the retailer filter can re-run it.
        set_user_last_query(message.from_user.id, search_query)
    status = await message.answer(t(lang, "search_loading"))

    try:
        container = METAX_LIFESPAN_MANAGER.get_metax_container()
        read_repo = await container.get_discounted_product_read_model_repository()
        if retailer_uuid is None:
            products, total = await read_repo.search_by_name(name=search_query, offset=0, limit=PAGE_SIZE)
        else:
            uow_provider = container.get_unit_of_work_provider()
            uow = await uow_provider.provide()
            async with uow:
                retailer = await uow.retailer_repo.get_by_uuid(UUID(retailer_uuid))
            selected_retailer_name = retailer.get_name()
            products, total = await read_repo.search_by_name_and_by_retailer_uuid(
                name=search_query,
                retailer_uuid=retailer_uuid,
                offset=0,
                limit=PAGE_SIZE,
            )
    except Exception:
        logger.exception("Search failed for query %r", search_query)
        await status.edit_text(t(lang, "search_error"))
        return

    if not products:
        await status.edit_text(
            t(lang, "search_empty", query=html.escape(display_query)),
            parse_mode=ParseMode.HTML,
        )
        return

    await status.delete()
    keyboard = search_result_keyboard(
        search_query,
        offset=0,
        total=total,
        language_code=lang,
        selected_retailer_name=selected_retailer_name,
    )
    await send_product_page(
        reply_target=message,
        products=products,
        total=total,
        offset=0,
        header=f"🔍 <b>«{html.escape(display_query)}»</b>",
        summary_label=t(lang, "results_found"),
        page_label=t(lang, "page"),
        image_unavailable=t(lang, "image_unavailable"),
        keyboard=keyboard,
        language_code=lang,
    )


async def load_categories(language_code: str) -> list[tuple[str, str]]:
    """Load all categories as ``(uuid, localized_name)`` pairs for the category menu.

    Returns:
        Category id/name pairs; names localized to ``language_code`` with an English fallback.
    """
    container = METAX_LIFESPAN_MANAGER.get_metax_container()
    uow_provider = container.get_unit_of_work_provider()
    uow = await uow_provider.provide()
    async with uow:
        categories = await uow.category_repo.all()
    return [
        (
            str(category.get_uuid()),
            localized_category_name(
                category.get_name(), category.get_name_hy(), category.get_name_ru(), language_code
            ),
        )
        for category in categories
    ]


async def categories_handler(message: Message) -> None:
    lang = get_user_language(message.from_user.id if message.from_user else None)
    categories = await load_categories(lang)
    if not categories:
        await message.answer(t(lang, "categories_none"))
        return
    await message.answer(t(lang, "categories_title"), reply_markup=categories_keyboard(categories))


async def help_handler(message: Message) -> None:
    lang = get_user_language(message.from_user.id if message.from_user else None)
    await message.answer(t(lang, "help"), parse_mode=ParseMode.HTML)


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    lang = get_user_language(message.from_user.id if message.from_user else None)
    await message.answer(
        t(lang, "choose_language"),
        parse_mode=ParseMode.HTML,
        reply_markup=language_keyboard(),
    )


@router.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    await help_handler(message)


@router.message(Command("search"))
async def search_handler(message: Message) -> None:
    if message.text is None:
        return
    parts = message.text.split(maxsplit=1)
    await run_search(message, parts[1] if len(parts) >= 2 else "")


@router.message(Command("categories"))
async def command_categories_handler(message: Message) -> None:
    await categories_handler(message)
