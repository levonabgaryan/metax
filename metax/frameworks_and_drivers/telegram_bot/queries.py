"""Data access for the bot.

The bot calls the application layer directly (DI container + repositories) rather than going through
the HTTP API, for latency. The HTTP JSON:API must stay at feature parity with what is used here.
"""

from __future__ import annotations

from uuid import UUID

from metax.core.application.ports.ddd_patterns.repository.read_models_repositories.discounted_product_read_model import (  # noqa: E501
    DiscountedProductReadModelRepository,
)
from metax.core.domain.entities.category.aggregate_root_entity import Category
from metax.core.domain.entities.retailer.aggregate_root_entity import Retailer
from metax.frameworks_and_drivers.telegram_bot.localization import localized_category_name
from metax_bootstrap import METAX_LIFESPAN_MANAGER


async def read_repository() -> DiscountedProductReadModelRepository:
    return await METAX_LIFESPAN_MANAGER.get_metax_container().get_discounted_product_read_model_repository()


async def load_retailer(retailer_uuid: str) -> Retailer:
    """Load one retailer; propagates ``EntityIsNotFoundError`` if it no longer exists.

    Returns:
        The retailer entity.
    """
    uow = await METAX_LIFESPAN_MANAGER.get_metax_container().get_unit_of_work_provider().provide()
    async with uow:
        return await uow.retailer_repo.get_by_uuid(UUID(retailer_uuid))


async def load_retailers() -> list[tuple[str, str]]:
    """Load every retailer for the filter menu.

    Returns:
        ``(uuid, name)`` pairs.
    """
    uow = await METAX_LIFESPAN_MANAGER.get_metax_container().get_unit_of_work_provider().provide()
    async with uow:
        return [(str(retailer.get_uuid()), retailer.get_name()) async for retailer in uow.retailer_repo.all()]


async def load_categories(language_code: str) -> list[tuple[str, str]]:
    """Load every category for the category menu.

    Returns:
        ``(uuid, name)`` pairs, names localized to ``language_code`` with an English fallback.
    """
    uow = await METAX_LIFESPAN_MANAGER.get_metax_container().get_unit_of_work_provider().provide()
    async with uow:
        categories = await uow.category_repo.all()
    return [(str(category.get_uuid()), _localized_name(category, language_code)) for category in categories]


async def load_category_name(category_uuid: str, language_code: str) -> str:
    """Load a category's name in the user's language (callback data is too small to carry it).

    Returns:
        The localized category name, falling back to the English name.
    """
    uow = await METAX_LIFESPAN_MANAGER.get_metax_container().get_unit_of_work_provider().provide()
    async with uow:
        category = await uow.category_repo.get_by_uuid(UUID(category_uuid))
    return _localized_name(category, language_code)


def _localized_name(category: Category, language_code: str) -> str:
    return localized_category_name(
        category.get_name(), category.get_name_hy(), category.get_name_ru(), language_code
    )
