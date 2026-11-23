"""Rendering a page of products: photo albums with captions, then a summary line with the keyboard."""

from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path
from urllib.parse import quote, urlsplit

import httpx
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
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
from metax.frameworks_and_drivers.telegram_bot.keyboards import PAGE_SIZE
from metax.frameworks_and_drivers.telegram_bot.localization import t

logger = logging.getLogger(__name__)

_LINK_PREVIEW_DISABLED = LinkPreviewOptions(is_disabled=True)

# Telegram hard limit on items per sendMediaGroup call.
_MEDIA_GROUP_MAX = 10


# Static placeholder shown in place of an image Telegram cannot fetch, so the album stays whole.
_PLACEHOLDER_BYTES = (Path(__file__).resolve().parent / "assets" / "no_image.png").read_bytes()

# Telegram reports a rejected album item as "...failed to send message #N..." (1-based).
_FAILED_ITEM_RE = re.compile(r"message #(\d+)")

# Hosts whose images Telegram's own fetcher cannot reliably retrieve. tntesakan.am publishes a
# dead IPv6 (AAAA) record and sits on slow reg.ru shared hosting, so Telegram's short-timeout,
# IPv6-preferring fetch times out — and, worse, Telegram caches that failure per-URL, so a page
# that timed out once (e.g. a category's first page, opened cold) stays broken while later pages
# opened against warm caches work. We can't change their hosting, so for these hosts we fetch the
# image ourselves through a CDN mirror (images.weserv.nl, on Cloudflare — healthy IPv6, fast IPv4
# edges) and upload the bytes to Telegram directly, so Telegram never fetches the flaky origin and
# has no failure to cache. The bytes live in memory only for the duration of the send — nothing is
# written to disk or accumulated. Every other host is still handed to Telegram as a plain URL.
_TELEGRAM_UNFETCHABLE_IMAGE_HOSTS = frozenset({"tntesakan.am", "www.tntesakan.am", "vlv.am", "www.vlv.am"})

# Timeout for our own server-side fetch of a CDN mirror image (well under Telegram's own window).
_CDN_FETCH_TIMEOUT = httpx.Timeout(20.0)


def _telegram_fetchable_url(image_url: str) -> str:
    """Return a URL Telegram can fetch, routing known-unfetchable hosts through an image CDN."""
    host = (urlsplit(image_url).hostname or "").lower()
    if host not in _TELEGRAM_UNFETCHABLE_IMAGE_HOSTS:
        return image_url
    # weserv takes the source without its scheme; the ssl: prefix forces an HTTPS origin fetch and
    # output=jpg normalises every format (incl. tntesakan's webp) to a Telegram-safe JPEG.
    source = image_url.split("://", 1)[-1]
    return "https://images.weserv.nl/?url=" + quote(f"ssl:{source}", safe="") + "&output=jpg"


async def _resolve_photo_ref(image_url: str) -> str | BufferedInputFile:
    """Return what to hand Telegram for a product image: a plain URL, or uploadable bytes.

    For hosts Telegram cannot reliably fetch we download the CDN-mirrored image ourselves (over
    the CDN's fast IPv4 edge) and return the bytes as an uploadable file, so Telegram never fetches
    the flaky origin and cannot cache a fetch failure. The bytes are held in memory only. If our
    own fetch fails we fall back to handing Telegram the CDN URL, so the image can still resolve.

    Returns:
        The original URL for fetchable hosts, or in-memory image bytes for unfetchable ones.
    """
    host = (urlsplit(image_url).hostname or "").lower()
    if host not in _TELEGRAM_UNFETCHABLE_IMAGE_HOSTS:
        return image_url
    cdn_url = _telegram_fetchable_url(image_url)
    try:
        async with httpx.AsyncClient(timeout=_CDN_FETCH_TIMEOUT, follow_redirects=True) as client:
            response = await client.get(cdn_url)
            response.raise_for_status()
    except httpx.HTTPError as err:
        logger.warning("CDN image fetch failed, falling back to URL | url=%r (%s)", cdn_url, err)
        return cdn_url
    return BufferedInputFile(response.content, filename="image.jpg")


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
        await reply_target.answer_photo(photo=only.media, caption=only.caption, parse_mode=ParseMode.HTML)
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
    reply_target: Message, items: list[tuple[str | InputFile, str]], image_unavailable: str
) -> None:
    """Send up to 10 ``(photo_ref, caption)`` items as a single album.

    ``photo_ref`` is either a URL Telegram fetches itself or in-memory bytes we upload. If Telegram
    rejects one (too large or unfetchable) it names the offending item, so we swap that slot for a
    static placeholder — captioned with ``image_unavailable`` — and re-send, keeping the album
    whole instead of degrading to one-by-one.
    """
    if not items:
        return

    media = [_photo_media(ref, caption) for ref, caption in items]
    for _attempt in range(len(media) + 1):
        try:
            await _send_album_or_photo(reply_target, media)
            return
        except TelegramBadRequest as err:
            index = _failed_media_index(err.message, len(media))
            if index is None:
                logger.warning("Album send failed; could not identify the bad image (%s)", err.message)
                break
            caption = items[index][1]
            logger.warning("Image rejected by Telegram, using placeholder (item #%d)", index + 1)
            media[index] = _placeholder_media(caption, image_unavailable)

    # Safety net: if the album still cannot be sent, fall back to text so nothing is lost.
    for _, caption in items:
        await reply_target.answer(caption, parse_mode=ParseMode.HTML, link_preview_options=_LINK_PREVIEW_DISABLED)


async def send_product_page(
    reply_target: Message,
    products: list[DiscountedProductReadModel],
    *,
    total: int,
    offset: int,
    header: str,
    keyboard: InlineKeyboardMarkup | None,
    language_code: str,
) -> None:
    """Send one page of products (as photo albums where possible) followed by a summary + keyboard."""
    # Group all photos into a single album (one API call) instead of one send per
    # product — cuts Telegram API calls ~5x and eases per-chat/global flood limits.
    photos: list[tuple[str, str]] = []
    text_only: list[str] = []
    for n, p in enumerate(products, start=offset + 1):
        text = format_product(p, n, language_code)
        image_url = p.get("image_url")
        if image_url and image_url.startswith(("http://", "https://")):
            photos.append((image_url, text))
        else:
            text_only.append(text)

    # Resolve each photo to what Telegram should receive — a plain URL, or in-memory bytes for
    # hosts Telegram can't fetch reliably. Resolve concurrently so a page of downloads costs one
    # round-trip's latency, not the sum.
    refs = await asyncio.gather(*(_resolve_photo_ref(url) for url, _ in photos))
    items: list[tuple[str | InputFile, str]] = [
        (ref, text) for ref, (_url, text) in zip(refs, photos, strict=True)
    ]

    image_unavailable = t(language_code, "image_unavailable")
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
    found, page_label = t(language_code, "results_found"), t(language_code, "page")
    summary = f"{header} — {found}: {total} • {page_label} {page}/{total_pages}"
    await reply_target.answer(
        summary,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
        link_preview_options=_LINK_PREVIEW_DISABLED,
    )
