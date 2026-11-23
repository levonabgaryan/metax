"""Callback query handlers: pagination, category browse, language selection and the retailer filter."""

from __future__ import annotations

import contextlib
import html
import logging
from typing import TYPE_CHECKING

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from metax.frameworks_and_drivers.telegram_bot.keyboards import (
    CategoryBrowseCB,
    LanguageSelectCB,
    OpenCategoriesCB,
    OpenStoresCB,
    RetailerClearCB,
    RetailerFilterMenuCB,
    RetailerSelectCB,
    SearchNavCB,
    StoreBrowseCB,
    StoreSearchCB,
    categories_keyboard,
    main_menu_keyboard,
    retailer_selection_keyboard,
    stores_keyboard,
)
from metax.frameworks_and_drivers.telegram_bot.localization import retailer_display_name, t
from metax.frameworks_and_drivers.telegram_bot.queries import load_categories, load_retailers
from metax.frameworks_and_drivers.telegram_bot.result_pages import (
    ResultPage,
    active_retailer_name,
    build_active_view_page,
    build_category_page,
    build_search_page,
    build_store_page,
    send_result_page,
)
from metax.frameworks_and_drivers.telegram_bot.user_state import UserSession, session_for

if TYPE_CHECKING:
    from collections.abc import Awaitable

logger = logging.getLogger(__name__)

router = Router()


async def _show_next_page(message: Message, session: UserSession, build: Awaitable[ResultPage]) -> None:
    """Show another page of the current result set below the previous one.

    The previous page's keyboard is removed so only the newest page is navigable.
    """
    try:
        page = await build
    except Exception:
        logger.exception("Loading a result page failed")
        await message.edit_text(t(session.language, "search_error"))
        return
    if page.is_empty:
        await message.answer(page.empty_text, parse_mode=ParseMode.HTML, reply_markup=page.empty_keyboard)
        return
    with contextlib.suppress(TelegramBadRequest):
        await message.edit_reply_markup(reply_markup=None)
    await send_result_page(message, page, session.language)


async def _show_intro_menu(message: Message, session: UserSession) -> None:
    with contextlib.suppress(TelegramBadRequest):
        await message.edit_text(
            t(session.language, "intro"),
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu_keyboard(
                language_code=session.language, selected_retailer_name=await active_retailer_name(session)
            ),
        )


async def _apply_retailer_filter(callback: CallbackQuery, retailer_uuid: str | None) -> None:
    """Set (or clear) the search narrowing and re-show the user's search or category with it applied.

    Only reachable from the narrowing controls under a search/category page, so re-running that view
    is what the user asked for. (Browsing a store is a separate action — see ``StoreBrowseCB``.) The
    picker message is replaced by fresh results; with no search or category yet, the intro menu is
    shown instead (now reflecting the new narrowing).
    """
    if not isinstance(callback.message, Message):
        return
    session = session_for(callback.from_user.id)
    session.retailer_uuid = retailer_uuid
    try:
        page = await build_active_view_page(session)
    except Exception:
        logger.exception("Re-running the active view after a filter change failed")
        await callback.message.edit_text(t(session.language, "search_error"))
        return
    if page is None:
        await _show_intro_menu(callback.message, session)
        return
    with contextlib.suppress(TelegramBadRequest):
        await callback.message.delete()
    await send_result_page(callback.message, page, session.language)


@router.callback_query(SearchNavCB.filter())
async def search_page_callback(callback: CallbackQuery, callback_data: SearchNavCB) -> None:
    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    session = session_for(callback.from_user.id)
    session.enter_search(callback_data.query)
    await _show_next_page(
        callback.message, session, build_search_page(session, callback_data.query, callback_data.offset)
    )


@router.callback_query(CategoryBrowseCB.filter())
async def category_browse_callback(callback: CallbackQuery, callback_data: CategoryBrowseCB) -> None:
    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    session = session_for(callback.from_user.id)
    # Mark category browse as the active view so a later retailer-filter change re-applies here.
    session.enter_category(callback_data.category_uuid)
    await _show_next_page(
        callback.message, session, build_category_page(session, callback_data.category_uuid, callback_data.offset)
    )


@router.callback_query(OpenCategoriesCB.filter())
async def open_categories_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    lang = session_for(callback.from_user.id).language
    categories = await load_categories(lang)
    with contextlib.suppress(TelegramBadRequest):
        if categories:
            await callback.message.edit_text(
                t(lang, "categories_title"), reply_markup=categories_keyboard(categories)
            )
        else:
            await callback.message.edit_text(t(lang, "categories_none"))


@router.callback_query(OpenStoresCB.filter())
async def open_stores_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    lang = session_for(callback.from_user.id).language
    retailers = await load_retailers()
    with contextlib.suppress(TelegramBadRequest):
        if retailers:
            await callback.message.edit_text(t(lang, "stores_title"), reply_markup=stores_keyboard(retailers))
        else:
            await callback.message.edit_text(t(lang, "stores_none"))


@router.callback_query(StoreBrowseCB.filter())
async def store_browse_callback(callback: CallbackQuery, callback_data: StoreBrowseCB) -> None:
    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    session = session_for(callback.from_user.id)
    # Deliberately no ``enter_*``: browsing a store leaves the last search/category (and the search
    # narrowing) untouched, so it can never re-run or rescope them.
    await _show_next_page(
        callback.message, session, build_store_page(session, callback_data.retailer_uuid, callback_data.offset)
    )


@router.callback_query(StoreSearchCB.filter())
async def store_search_callback(callback: CallbackQuery, callback_data: StoreSearchCB) -> None:
    """Narrow the next typed search to the store being browsed, and say so with a way to undo it."""
    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    session = session_for(callback.from_user.id)
    session.retailer_uuid = callback_data.retailer_uuid
    retailer_name = await active_retailer_name(session)
    if retailer_name is None:  # the store vanished between the tap and now
        await _show_intro_menu(callback.message, session)
        return
    with contextlib.suppress(TelegramBadRequest):
        await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        t(session.language, "store_search_prompt", retailer=html.escape(retailer_display_name(retailer_name))),
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(language_code=session.language, selected_retailer_name=retailer_name),
    )


@router.callback_query(LanguageSelectCB.filter())
async def language_select_callback(callback: CallbackQuery, callback_data: LanguageSelectCB) -> None:
    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    session = session_for(callback.from_user.id)
    session.set_language(callback_data.language_code)
    await _show_intro_menu(callback.message, session)


@router.callback_query(RetailerFilterMenuCB.filter())
async def retailer_filter_menu_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    session = session_for(callback.from_user.id)
    retailers = await load_retailers()
    with contextlib.suppress(TelegramBadRequest):
        await callback.message.edit_text(
            f"{t(session.language, 'choose_retailer')}\n{t(session.language, 'retailer_filter_hint')}",
            parse_mode=ParseMode.HTML,
            reply_markup=retailer_selection_keyboard(
                retailers, language_code=session.language, selected_uuid=session.retailer_uuid
            ),
        )


@router.callback_query(RetailerSelectCB.filter())
async def retailer_select_callback(callback: CallbackQuery, callback_data: RetailerSelectCB) -> None:
    await callback.answer()
    await _apply_retailer_filter(callback, callback_data.retailer_uuid)


@router.callback_query(RetailerClearCB.filter())
async def retailer_clear_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    await _apply_retailer_filter(callback, None)
