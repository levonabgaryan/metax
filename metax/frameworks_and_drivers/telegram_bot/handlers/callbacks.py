"""Callback query handlers: search pagination and language selection."""

from __future__ import annotations

import html
import logging
from uuid import UUID

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from metax.frameworks_and_drivers.telegram_bot.handlers.commands import send_product_page
from metax.frameworks_and_drivers.telegram_bot.keyboards import (
    LanguageSelectCB,
    PAGE_SIZE,
    RetailerClearCB,
    RetailerFilterMenuCB,
    RetailerSelectCB,
    SearchNavCB,
    retailer_filter_keyboard,
    retailer_selection_keyboard,
    search_result_keyboard,
)
from metax.frameworks_and_drivers.telegram_bot.localization import (
    get_user_language,
    get_user_retailer_filter,
    set_user_language,
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


async def _load_retailers() -> list[tuple[str, str]]:
    container = METAX_LIFESPAN_MANAGER.get_metax_container()
    uow_provider = container.get_unit_of_work_provider()
    uow = await uow_provider.provide()
    async with uow:
        retailers = [r async for r in uow.retailer_repo.all()]
    return [(str(retailer.get_uuid()), retailer.get_name()) for retailer in retailers]


@router.callback_query(LanguageSelectCB.filter())
async def language_select_callback(callback: CallbackQuery, callback_data: LanguageSelectCB) -> None:
    await callback.answer()
    if callback.message is None or callback.from_user is None:
        return

    set_user_language(callback.from_user.id, callback_data.language_code)
    selected_retailer_name = await _load_retailer_name(get_user_retailer_filter(callback.from_user.id))
    try:
        await callback.message.edit_text(
            t(callback_data.language_code, "intro"),
            parse_mode=ParseMode.HTML,
            reply_markup=retailer_filter_keyboard(
                language_code=callback_data.language_code,
                selected_retailer_name=selected_retailer_name,
            ),
        )
    except TelegramBadRequest:
        pass


@router.callback_query(RetailerFilterMenuCB.filter())
async def retailer_filter_menu_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is None or callback.from_user is None:
        return

    lang = get_user_language(callback.from_user.id)
    retailers = await _load_retailers()
    try:
        await callback.message.edit_text(
            f"{t(lang, 'choose_retailer')}\n{t(lang, 'retailer_filter_hint')}",
            parse_mode=ParseMode.HTML,
            reply_markup=retailer_selection_keyboard(retailers, language_code=lang),
        )
    except TelegramBadRequest:
        pass


@router.callback_query(RetailerSelectCB.filter())
async def retailer_select_callback(callback: CallbackQuery, callback_data: RetailerSelectCB) -> None:
    await callback.answer()
    if callback.message is None or callback.from_user is None:
        return

    set_user_retailer_filter(callback.from_user.id, callback_data.retailer_uuid)
    lang = get_user_language(callback.from_user.id)
    retailer_name = await _load_retailer_name(callback_data.retailer_uuid)
    try:
        await callback.message.edit_text(
            t(lang, "intro"),
            parse_mode=ParseMode.HTML,
            reply_markup=retailer_filter_keyboard(language_code=lang, selected_retailer_name=retailer_name),
        )
    except TelegramBadRequest:
        pass


@router.callback_query(RetailerClearCB.filter())
async def retailer_clear_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is None or callback.from_user is None:
        return

    set_user_retailer_filter(callback.from_user.id, None)
    lang = get_user_language(callback.from_user.id)
    try:
        await callback.message.edit_text(
            t(lang, "intro"),
            parse_mode=ParseMode.HTML,
            reply_markup=retailer_filter_keyboard(language_code=lang, selected_retailer_name=None),
        )
    except TelegramBadRequest:
        pass


@router.callback_query(SearchNavCB.filter())
async def search_page_callback(callback: CallbackQuery, callback_data: SearchNavCB) -> None:
    await callback.answer()
    if callback.message is None:
        return

    lang = get_user_language(callback.from_user.id if callback.from_user else None)
    query = callback_data.query
    offset = callback_data.offset

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

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

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
        keyboard=keyboard,
    )
