"""Command handlers: /start, /help, /search, /categories."""

from __future__ import annotations

import html
import logging
from uuid import UUID

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import LinkPreviewOptions, Message

from metax.core.application.read_models.discounted_product import DiscountedProductReadModel
from metax.frameworks_and_drivers.telegram_bot.formatters import format_product
from metax.frameworks_and_drivers.telegram_bot.keyboards import (
    PAGE_SIZE,
    clamp_query,
    language_keyboard,
    search_result_keyboard,
)
from metax.frameworks_and_drivers.telegram_bot.localization import (
    get_user_language,
    get_user_retailer_filter,
    t,
)
from metax_bootstrap import METAX_LIFESPAN_MANAGER

logger = logging.getLogger(__name__)

router = Router()

_LINK_PREVIEW_DISABLED = LinkPreviewOptions(is_disabled=True)


async def send_product_page(
    reply_target: Message,
    products: list[DiscountedProductReadModel],
    total: int,
    offset: int,
    header: str,
    summary_label: str,
    page_label: str,
    keyboard,
) -> None:
    for n, p in enumerate(products, start=offset + 1):
        image_url = p.get("image_url")
        text = format_product(p, n)
        sent = False

        if image_url and image_url.startswith(("http://", "https://")):
            try:
                await reply_target.answer_photo(
                    photo=image_url,
                    caption=text,
                    parse_mode=ParseMode.HTML,
                )
                sent = True
            except TelegramBadRequest as photo_err:
                try:
                    await reply_target.answer_document(
                        document=image_url,
                        caption=text,
                        parse_mode=ParseMode.HTML,
                    )
                    sent = True
                except TelegramBadRequest as doc_err:
                    logger.warning(
                        "Both photo and document failed for %r | photo=%s | doc=%s | url=%r",
                        p.get("name"), photo_err, doc_err, image_url,
                    )
                except Exception:
                    logger.warning("answer_document failed for %r", p.get("name"), exc_info=True)
            except Exception:
                logger.warning("answer_photo failed for %r", p.get("name"), exc_info=True)

        if not sent:
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
        keyboard=keyboard,
    )


async def categories_handler(message: Message) -> None:
    lang = get_user_language(message.from_user.id if message.from_user else None)
    await message.answer(t(lang, "categories_disabled"))


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
