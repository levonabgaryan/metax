"""Building and sending paginated result pages: name search and category browse.

Every handler that shows products (a new search, pagination, a retailer-filter change) goes through
``build_*_page`` → ``send_result_page`` so they all apply the user's filter, headers and keyboards the
same way. ``build_*`` performs the I/O and may raise; callers decide how to report a failure in their
own UI context.
"""

from __future__ import annotations

import html
import logging
from dataclasses import dataclass

from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, Message

from metax.core.application.ports.ddd_patterns.repository.errors import EntityIsNotFoundError
from metax.core.application.read_models.discounted_product import DiscountedProductReadModel
from metax.frameworks_and_drivers.telegram_bot.keyboards import (
    PAGE_SIZE,
    category_nav_keyboard,
    search_result_keyboard,
)
from metax.frameworks_and_drivers.telegram_bot.localization import t
from metax.frameworks_and_drivers.telegram_bot.product_page import send_product_page
from metax.frameworks_and_drivers.telegram_bot.queries import load_category_name, load_retailer, read_repository
from metax.frameworks_and_drivers.telegram_bot.user_state import UserSession

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResultPage:
    products: list[DiscountedProductReadModel]
    total: int
    offset: int
    header: str
    keyboard: InlineKeyboardMarkup
    # Shown instead of the page when nothing matched.
    empty_text: str

    @property
    def is_empty(self) -> bool:
        return not self.products


async def active_retailer_name(session: UserSession) -> str | None:
    """Resolve the user's retailer filter to a name, dropping the filter if the retailer is gone.

    A retailer deleted after the user selected it would otherwise make every search fail until the
    user clears the filter by hand.

    Returns:
        The filtered retailer's name, or ``None`` when no (valid) filter is set.
    """
    if session.retailer_uuid is None:
        return None
    try:
        return (await load_retailer(session.retailer_uuid)).get_name()
    except EntityIsNotFoundError:
        logger.info("Dropping retailer filter %s — retailer no longer exists", session.retailer_uuid)
        session.retailer_uuid = None
        return None


async def build_search_page(session: UserSession, query: str, offset: int = 0) -> ResultPage:
    retailer_name = await active_retailer_name(session)
    products, total = await (await read_repository()).search_by_name(
        query, retailer_uuid=session.retailer_uuid, offset=offset, limit=PAGE_SIZE
    )
    escaped_query = html.escape(query)
    return ResultPage(
        products=products,
        total=total,
        offset=offset,
        header=f"🔍 <b>«{escaped_query}»</b>",
        keyboard=search_result_keyboard(
            query, offset, total, language_code=session.language, selected_retailer_name=retailer_name
        ),
        empty_text=t(session.language, "search_empty", query=escaped_query),
    )


async def build_category_page(session: UserSession, category_uuid: str, offset: int = 0) -> ResultPage:
    retailer_name = await active_retailer_name(session)
    # Most-confidently classified products first, narrowed to the active retailer filter when set.
    products, total = await (await read_repository()).search_by_category_uuid(
        category_uuid, retailer_uuid=session.retailer_uuid, offset=offset, limit=PAGE_SIZE
    )
    category_name = await load_category_name(category_uuid, session.language)
    return ResultPage(
        products=products,
        total=total,
        offset=offset,
        header=f"🏷 <b>{html.escape(category_name)}</b>",
        keyboard=category_nav_keyboard(
            category_uuid, offset, total, language_code=session.language, selected_retailer_name=retailer_name
        ),
        empty_text=t(session.language, "category_empty"),
    )


async def build_active_view_page(session: UserSession) -> ResultPage | None:
    """Rebuild the first page of whatever the user is currently looking at (search or category).

    Returns:
        The page, or ``None`` if the user has no active view yet.
    """
    if session.last_category_uuid is not None:
        return await build_category_page(session, session.last_category_uuid)
    if session.last_query is not None:
        return await build_search_page(session, session.last_query)
    return None


async def send_result_page(target: Message, page: ResultPage, language_code: str) -> None:
    if page.is_empty:
        await target.answer(page.empty_text, parse_mode=ParseMode.HTML)
        return
    await send_product_page(
        target,
        page.products,
        total=page.total,
        offset=page.offset,
        header=page.header,
        keyboard=page.keyboard,
        language_code=language_code,
    )
