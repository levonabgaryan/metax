"""Command handlers: /start, /help, /search, /categories."""

from __future__ import annotations

import html
import logging

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import LinkPreviewOptions, Message

from metax.core.application.read_models.discounted_product import DiscountedProductReadModel
from metax.frameworks_and_drivers.telegram_bot.formatters import format_product
from metax.frameworks_and_drivers.telegram_bot.keyboards import (
    CATEGORIES_BTN,
    HELP_BTN,
    PAGE_SIZE,
    categories_keyboard,
    clamp_query,
    main_menu_keyboard,
    search_nav_keyboard,
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
        f"{header} — найдено: {total} • Стр. {page}/{total_pages}",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
        link_preview_options=_LINK_PREVIEW_DISABLED,
    )


async def run_search(message: Message, raw_query: str) -> None:
    display_query = raw_query.strip()
    if not display_query:
        await message.answer(
            "Напишите название товара.\nПример: <code>телефон</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    search_query = clamp_query(display_query)
    status = await message.answer("🔍 Ищу…")

    try:
        container = METAX_LIFESPAN_MANAGER.get_metax_container()
        read_repo = await container.get_discounted_product_read_model_repository()
        products, total = await read_repo.search_by_name(name=search_query, offset=0, limit=PAGE_SIZE)
    except Exception:
        logger.exception("Search failed for query %r", search_query)
        await status.edit_text("⚠️ Ошибка при поиске. Попробуйте позже.")
        return

    if not products:
        await status.edit_text(
            f"🔍 <b>«{html.escape(display_query)}»</b> — найдено: 0\n\nПо этому запросу ничего не найдено.",
            parse_mode=ParseMode.HTML,
        )
        return

    await status.delete()
    keyboard = search_nav_keyboard(search_query, offset=0, total=total)
    await send_product_page(
        reply_target=message,
        products=products,
        total=total,
        offset=0,
        header=f"🔍 <b>«{html.escape(display_query)}»</b>",
        keyboard=keyboard,
    )


async def categories_handler(message: Message) -> None:
    status = await message.answer("📂 Загружаю категории…")
    try:
        container = METAX_LIFESPAN_MANAGER.get_metax_container()
        uow_provider = container.get_unit_of_work_provider()
        uow = await uow_provider.provide()
        async with uow:
            categories = await uow.category_repo.all()
    except Exception:
        logger.exception("Failed to load categories")
        await status.edit_text("⚠️ Не удалось загрузить категории. Попробуйте позже.")
        return

    if not categories:
        await status.edit_text("ℹ️ Категории пока не добавлены.")
        return

    cat_pairs = [(str(cat.get_uuid()), cat.get_name()) for cat in categories]
    await status.edit_text(
        "<b>Выберите категорию:</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=categories_keyboard(cat_pairs),
    )


async def help_handler(message: Message) -> None:
    await message.answer(
        "<b>Metax Bot</b>\n\n"
        "Просто напишите название товара — я найду скидки в Yerevan City и SAS AM.\n\n"
        "Кнопка <b>Категории</b> — просмотр по разделам.\n\n"
        "Навигация по страницам: кнопки <b>← →</b>.",
        parse_mode=ParseMode.HTML,
    )


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        "<b>Metax Bot</b> 🛒\n\n"
        "Нахожу лучшие скидки в Yerevan City и SAS AM.\n\n"
        "Напишите название товара — и я найду скидки.",
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(),
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
