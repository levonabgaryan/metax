"""Callback query handlers: search/category pagination."""

from __future__ import annotations

import html
import logging

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from metax.frameworks_and_drivers.telegram_bot.handlers.commands import send_product_page
from metax.frameworks_and_drivers.telegram_bot.keyboards import (
    PAGE_SIZE,
    BackToCategoriesCB,
    CategoryBrowseCB,
    SearchNavCB,
    categories_keyboard,
    category_nav_keyboard,
    search_nav_keyboard,
)
from metax_bootstrap import METAX_LIFESPAN_MANAGER

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(SearchNavCB.filter())
async def search_page_callback(callback: CallbackQuery, callback_data: SearchNavCB) -> None:
    await callback.answer()
    if callback.message is None:
        return

    query = callback_data.query
    offset = callback_data.offset

    try:
        container = METAX_LIFESPAN_MANAGER.get_metax_container()
        read_repo = await container.get_discounted_product_read_model_repository()
        products, total = await read_repo.search_by_name(name=query, offset=offset, limit=PAGE_SIZE)
    except Exception:
        logger.exception("Paginated search failed for query %r offset %d", query, offset)
        await callback.message.edit_text("⚠️ Ошибка при загрузке страницы.")
        return

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    keyboard = search_nav_keyboard(query, offset=offset, total=total)
    await send_product_page(
        reply_target=callback.message,
        products=products,
        total=total,
        offset=offset,
        header=f"🔍 <b>«{html.escape(query)}»</b>",
        keyboard=keyboard,
    )


@router.callback_query(CategoryBrowseCB.filter())
async def category_browse_callback(callback: CallbackQuery, callback_data: CategoryBrowseCB) -> None:
    await callback.answer()
    if callback.message is None:
        return

    category_uuid = callback_data.category_uuid
    category_name = callback_data.category_name
    offset = callback_data.offset

    try:
        container = METAX_LIFESPAN_MANAGER.get_metax_container()
        read_repo = await container.get_discounted_product_read_model_repository()
        products, total = await read_repo.search_by_category_uuid(
            category_uuid=category_uuid, offset=offset, limit=PAGE_SIZE
        )
    except Exception:
        logger.exception("Category browse failed for uuid %r", category_uuid)
        await callback.message.edit_text("⚠️ Ошибка при загрузке категории.")
        return

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    keyboard = category_nav_keyboard(
        category_uuid=category_uuid,
        category_name=category_name,
        offset=offset,
        total=total,
    )
    await send_product_page(
        reply_target=callback.message,
        products=products,
        total=total,
        offset=offset,
        header=f"🏷 <b>{html.escape(category_name)}</b>",
        keyboard=keyboard,
    )


@router.callback_query(BackToCategoriesCB.filter())
async def back_to_categories_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is None:
        return

    try:
        container = METAX_LIFESPAN_MANAGER.get_metax_container()
        uow_provider = container.get_unit_of_work_provider()
        uow = await uow_provider.provide()
        async with uow:
            categories = await uow.category_repo.all()
    except Exception:
        logger.exception("Failed to reload categories")
        await callback.message.edit_text("⚠️ Не удалось загрузить категории.")
        return

    if not categories:
        await callback.message.edit_text("ℹ️ Категории пока не добавлены.")
        return

    cat_pairs = [(str(cat.get_uuid()), cat.get_name()) for cat in categories]
    try:
        await callback.message.edit_text(
            "<b>Выберите категорию:</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=categories_keyboard(cat_pairs),
        )
    except TelegramBadRequest:
        pass
