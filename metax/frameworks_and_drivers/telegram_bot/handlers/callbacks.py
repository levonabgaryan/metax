"""Callback query handlers: search pagination and language selection."""

from __future__ import annotations

import contextlib
import html
import logging
from uuid import UUID

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from metax.frameworks_and_drivers.telegram_bot.handlers.commands import load_categories, send_product_page
from metax.frameworks_and_drivers.telegram_bot.keyboards import (
    PAGE_SIZE,
    CategoryBrowseCB,
    LanguageSelectCB,
    OpenCategoriesCB,
    RetailerClearCB,
    RetailerFilterMenuCB,
    RetailerSelectCB,
    SearchNavCB,
    categories_keyboard,
    category_nav_keyboard,
    retailer_filter_keyboard,
    retailer_selection_keyboard,
    search_result_keyboard,
)
from metax.frameworks_and_drivers.telegram_bot.localization import (
    get_user_language,
    get_user_last_query,
    get_user_retailer_filter,
    localized_category_name,
    set_user_language,
    set_user_last_query,
    set_user_retailer_filter,
    t,
)
from metax_bootstrap import METAX_LIFESPAN_MANAGER

logger = logging.getLogger(__name__)

router = Router()


async def _load_retailer_name(retailer_uuid: str | None) -> str | None:
    if retailer_uuid is None:
        return None
    container = METAX_LIFESPAN_MANAGER.get_metax_container()
    uow_provider = container.get_unit_of_work_provider()
    uow = await uow_provider.provide()
    async with uow:
        retailer = await uow.retailer_repo.get_by_uuid(UUID(retailer_uuid))
    return retailer.get_name()


async def _load_category_name(category_uuid: str, language_code: str) -> str:
    """Load a category's name in the user's language, so the header isn't limited by callback size.

    Returns:
        The localized category name, falling back to the English name when no translation exists.
    """
    container = METAX_LIFESPAN_MANAGER.get_metax_container()
    uow_provider = container.get_unit_of_work_provider()
    uow = await uow_provider.provide()
    async with uow:
        category = await uow.category_repo.get_by_uuid(UUID(category_uuid))
    return localized_category_name(
        category.get_name(), category.get_name_hy(), category.get_name_ru(), language_code
    )


async def _load_retailers() -> list[tuple[str, str]]:
    container = METAX_LIFESPAN_MANAGER.get_metax_container()
    uow_provider = container.get_unit_of_work_provider()
    uow = await uow_provider.provide()
    async with uow:
        retailers = [r async for r in uow.retailer_repo.all()]
    return [(str(retailer.get_uuid()), retailer.get_name()) for retailer in retailers]


async def _rerun_search_after_filter_change(callback: CallbackQuery, query: str, lang: str) -> None:
    """Re-run the user's last search with the current retailer filter, replacing the menu with results."""
    if not isinstance(callback.message, Message):
        return
    retailer_uuid = get_user_retailer_filter(callback.from_user.id)
    selected_retailer_name = await _load_retailer_name(retailer_uuid)
    try:
        container = METAX_LIFESPAN_MANAGER.get_metax_container()
        read_repo = await container.get_discounted_product_read_model_repository()
        if retailer_uuid is None:
            products, total = await read_repo.search_by_name(name=query, offset=0, limit=PAGE_SIZE)
        else:
            products, total = await read_repo.search_by_name_and_by_retailer_uuid(
                name=query, retailer_uuid=retailer_uuid, offset=0, limit=PAGE_SIZE
            )
    except Exception:
        logger.exception("Filter re-run search failed for query %r", query)
        await callback.message.edit_text(t(lang, "search_error"))
        return

    # Drop the filter-menu message and post fresh results in its place.
    with contextlib.suppress(TelegramBadRequest):
        await callback.message.delete()

    if not products:
        await callback.message.answer(
            t(lang, "search_empty", query=html.escape(query)), parse_mode=ParseMode.HTML
        )
        return

    keyboard = search_result_keyboard(
        query,
        offset=0,
        total=total,
        language_code=lang,
        selected_retailer_name=selected_retailer_name,
    )
    await send_product_page(
        reply_target=callback.message,
        products=products,
        total=total,
        offset=0,
        header=f"🔍 <b>«{html.escape(query)}»</b>",
        summary_label=t(lang, "results_found"),
        page_label=t(lang, "page"),
        image_unavailable=t(lang, "image_unavailable"),
        keyboard=keyboard,
        language_code=lang,
    )


@router.callback_query(CategoryBrowseCB.filter())
async def category_browse_callback(callback: CallbackQuery, callback_data: CategoryBrowseCB) -> None:
    await callback.answer()
    if not isinstance(callback.message, Message):
        return

    lang = get_user_language(callback.from_user.id)
    category_uuid = callback_data.category_uuid
    offset = callback_data.offset
    try:
        container = METAX_LIFESPAN_MANAGER.get_metax_container()
        read_repo = await container.get_discounted_product_read_model_repository()
        # Products are returned most-confident-first (closest to the category prototype).
        products, total = await read_repo.search_by_category_uuid(
            category_uuid, offset=offset, limit=PAGE_SIZE
        )
    except Exception:
        logger.exception("Category browse failed for %r offset %d", category_uuid, offset)
        await callback.message.edit_text(t(lang, "search_error"))
        return

    if not products:
        await callback.message.answer(t(lang, "category_empty"))
        return

    with contextlib.suppress(TelegramBadRequest):
        await callback.message.edit_reply_markup(reply_markup=None)

    category_name = await _load_category_name(category_uuid, lang)
    keyboard = category_nav_keyboard(
        category_uuid=category_uuid,
        offset=offset,
        total=total,
        language_code=lang,
    )
    await send_product_page(
        reply_target=callback.message,
        products=products,
        total=total,
        offset=offset,
        header=f"🏷 <b>{html.escape(category_name)}</b>",
        summary_label=t(lang, "results_found"),
        page_label=t(lang, "page"),
        image_unavailable=t(lang, "image_unavailable"),
        keyboard=keyboard,
        language_code=lang,
    )


@router.callback_query(OpenCategoriesCB.filter())
async def open_categories_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if not isinstance(callback.message, Message):
        return

    lang = get_user_language(callback.from_user.id)
    categories = await load_categories(lang)
    if not categories:
        with contextlib.suppress(TelegramBadRequest):
            await callback.message.edit_text(t(lang, "categories_none"))
        return
    with contextlib.suppress(TelegramBadRequest):
        await callback.message.edit_text(
            t(lang, "categories_title"), reply_markup=categories_keyboard(categories)
        )


@router.callback_query(LanguageSelectCB.filter())
async def language_select_callback(callback: CallbackQuery, callback_data: LanguageSelectCB) -> None:
    await callback.answer()
    if not isinstance(callback.message, Message):
        return

    set_user_language(callback.from_user.id, callback_data.language_code)
    selected_retailer_name = await _load_retailer_name(get_user_retailer_filter(callback.from_user.id))
    with contextlib.suppress(TelegramBadRequest):
        await callback.message.edit_text(
            t(callback_data.language_code, "intro"),
            parse_mode=ParseMode.HTML,
            reply_markup=retailer_filter_keyboard(
                language_code=callback_data.language_code,
                selected_retailer_name=selected_retailer_name,
            ),
        )


@router.callback_query(RetailerFilterMenuCB.filter())
async def retailer_filter_menu_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if not isinstance(callback.message, Message):
        return

    lang = get_user_language(callback.from_user.id)
    retailers = await _load_retailers()
    selected_uuid = get_user_retailer_filter(callback.from_user.id)
    with contextlib.suppress(TelegramBadRequest):
        await callback.message.edit_text(
            f"{t(lang, 'choose_retailer')}\n{t(lang, 'retailer_filter_hint')}",
            parse_mode=ParseMode.HTML,
            reply_markup=retailer_selection_keyboard(
                retailers, language_code=lang, selected_uuid=selected_uuid
            ),
        )


@router.callback_query(RetailerSelectCB.filter())
async def retailer_select_callback(callback: CallbackQuery, callback_data: RetailerSelectCB) -> None:
    await callback.answer()
    if not isinstance(callback.message, Message):
        return

    set_user_retailer_filter(callback.from_user.id, callback_data.retailer_uuid)
    lang = get_user_language(callback.from_user.id)
    last_query = get_user_last_query(callback.from_user.id)
    if last_query:
        await _rerun_search_after_filter_change(callback, last_query, lang)
        return
    retailer_name = await _load_retailer_name(callback_data.retailer_uuid)
    with contextlib.suppress(TelegramBadRequest):
        await callback.message.edit_text(
            t(lang, "intro"),
            parse_mode=ParseMode.HTML,
            reply_markup=retailer_filter_keyboard(language_code=lang, selected_retailer_name=retailer_name),
        )


@router.callback_query(RetailerClearCB.filter())
async def retailer_clear_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if not isinstance(callback.message, Message):
        return

    set_user_retailer_filter(callback.from_user.id, None)
    lang = get_user_language(callback.from_user.id)
    last_query = get_user_last_query(callback.from_user.id)
    if last_query:
        await _rerun_search_after_filter_change(callback, last_query, lang)
        return
    with contextlib.suppress(TelegramBadRequest):
        await callback.message.edit_text(
            t(lang, "intro"),
            parse_mode=ParseMode.HTML,
            reply_markup=retailer_filter_keyboard(language_code=lang, selected_retailer_name=None),
        )


@router.callback_query(SearchNavCB.filter())
async def search_page_callback(callback: CallbackQuery, callback_data: SearchNavCB) -> None:
    await callback.answer()
    if not isinstance(callback.message, Message):
        return

    lang = get_user_language(callback.from_user.id if callback.from_user else None)
    query = callback_data.query
    offset = callback_data.offset
    if callback.from_user:
        set_user_last_query(callback.from_user.id, query)

    try:
        container = METAX_LIFESPAN_MANAGER.get_metax_container()
        read_repo = await container.get_discounted_product_read_model_repository()
        retailer_uuid = get_user_retailer_filter(callback.from_user.id if callback.from_user else None)
        selected_retailer_name = await _load_retailer_name(retailer_uuid)
        if retailer_uuid is None:
            products, total = await read_repo.search_by_name(name=query, offset=offset, limit=PAGE_SIZE)
        else:
            products, total = await read_repo.search_by_name_and_by_retailer_uuid(
                name=query,
                retailer_uuid=retailer_uuid,
                offset=offset,
                limit=PAGE_SIZE,
            )
    except Exception:
        logger.exception("Paginated search failed for query %r offset %d", query, offset)
        await callback.message.edit_text(t(lang, "search_error"))
        return

    with contextlib.suppress(TelegramBadRequest):
        await callback.message.edit_reply_markup(reply_markup=None)

    keyboard = search_result_keyboard(
        query,
        offset=offset,
        total=total,
        language_code=lang,
        selected_retailer_name=selected_retailer_name,
    )
    await send_product_page(
        reply_target=callback.message,
        products=products,
        total=total,
        offset=offset,
        header=f"🔍 <b>«{html.escape(query)}»</b>",
        summary_label=t(lang, "results_found"),
        page_label=t(lang, "page"),
        image_unavailable=t(lang, "image_unavailable"),
        keyboard=keyboard,
        language_code=lang,
    )
