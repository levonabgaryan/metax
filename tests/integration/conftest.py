import asyncio
from decimal import Decimal
from typing import AsyncIterator
from uuid import UUID, uuid4

import pytest

from backend.core.application.ports.patterns.unit_of_work import UnitOfWork
from backend.core.domain.entities.category_entity.category import Category, CategoryHelperWords
from backend.core.domain.entities.discounted_product_entity.discounted_product import (
    DiscountedProduct,
    PriceDetails,
)
from backend.core.domain.entities.retailer_entity.retailer import Retailer
from backend.frameworks_and_drivers.di.boostrap import main_container
from backend.frameworks_and_drivers.di.boostrap import MainContainer
from backend.frameworks_and_drivers.di.commands_handlers_container import (
    CategoryCommandsHandlersContainer,
    RetailerCommandsHandlersContainer,
)
from backend.frameworks_and_drivers.di.event_handlers_container import (
    DiscountedProductEventHandlersContainer,
    RetailerEventHandlersContainer,
    CategoryEventHandlersContainer,
)
from backend.frameworks_and_drivers.di.patterns_container import PatternsContainer
from backend.frameworks_and_drivers.di.use_cases_container import DiscountedProductUseCasesContainer


@pytest.fixture(scope="session")
def container() -> MainContainer:
    return main_container


@pytest.fixture
def unit_of_work(container: MainContainer) -> UnitOfWork:
    patterns: PatternsContainer = container.patterns()
    return patterns.unit_of_work()


@pytest.fixture
def category_commands_handlers(container: MainContainer) -> CategoryCommandsHandlersContainer:
    return container.commands_handlers().category()


@pytest.fixture
def retailer_commands_handlers(container: MainContainer) -> RetailerCommandsHandlersContainer:
    return container.commands_handlers().retailer()


@pytest.fixture
def discounted_product_event_handlers(container: MainContainer) -> DiscountedProductEventHandlersContainer:
    return container.event_handlers().discounted_product()


@pytest.fixture
def retailer_event_handlers(container: MainContainer) -> RetailerEventHandlersContainer:
    return container.event_handlers().retailer()


@pytest.fixture
def category_event_handlers(container: MainContainer) -> CategoryEventHandlersContainer:
    return container.event_handlers().category()


@pytest.fixture
def discounted_product_use_cases(container: MainContainer) -> DiscountedProductUseCasesContainer:
    return container.use_cases().discounted_product()


def make_category_entity(
    category_uuid: UUID | None = None,
    name: str = "test_category_name",
    helper_words: CategoryHelperWords = CategoryHelperWords(words=frozenset(["test_word1", " test_word2"])),
) -> Category:
    return Category(
        name=name,
        category_uuid=category_uuid or uuid4(),
        helper_words=helper_words,
    )


def make_retailer_entity(
    retailer_uuid: UUID | None = None,
    name: str = "test_retailer_name",
    url: str = "test_retailer_url",
    phone_number: str = "test_retailer_phone_number",
) -> Retailer:
    return Retailer(retailer_uuid=retailer_uuid or uuid4(), name=name, phone_number=phone_number, url=url)


def make_discounted_product_entity(
    retailer_uuid: UUID,
    category_uuid: UUID | None = None,
    discounted_product_uuid: UUID | None = None,
    name: str = "test_discounted_product_name",
    price_details: PriceDetails | None = None,
    url: str = "test_discounted_product_url",
) -> DiscountedProduct:
    price_details = price_details or PriceDetails(
        real_price=Decimal("100"),
        discounted_price=Decimal("50"),
    )
    return DiscountedProduct(
        name=name,
        retailer_uuid=retailer_uuid,
        category_uuid=category_uuid,
        discounted_product_uuid=discounted_product_uuid or uuid4(),
        price_details=price_details,
        url=url,
    )


async def mock_create_many_discounted_products_from_retailer(
    retailer_uuid: UUID, discounted_product_counts: int = 4, batch_size: int = 1
) -> AsyncIterator[list[DiscountedProduct]]:
    # Mock function for IDiscountedProductFactory.create_many_from_retailer
    discounted_products = []
    for i in range(discounted_product_counts):
        discounted_product = make_discounted_product_entity(retailer_uuid=retailer_uuid)
        discounted_products.append(discounted_product)

        if len(discounted_products) == batch_size:
            yield discounted_products
            discounted_products = []
            await asyncio.sleep(0.0)

    if discounted_products:
        yield discounted_products
