from __future__ import annotations
import re
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import AsyncIterator, TypedDict
from uuid import UUID

from discount_service.core.domain.entities.discounted_product_entity.discounted_product import (
    DiscountedProduct,
    PriceDetails,
)
from discount_service.core.domain.entities.retailer_entity.retailer import Retailer


class ScrapperAdapter(ABC):
    def __init__(self, data_source_url: str) -> None:
        self._data_source_url = data_source_url

    @abstractmethod
    def fetch(self, started_time: datetime, retailer: Retailer) -> AsyncIterator[DiscountedProduct]:
        pass

    @staticmethod
    def _clean_discounted_product_name(text: str) -> str:
        """
        Normalize product name:
        - lowercase
        - remove special symbols
        - keep latin, cyrillic, armenian letters and digits
        - normalize spaces
        """
        text = text.lower()
        text = re.sub(
            r"[^a-z0-9а-яёա-ֆ]+",
            " ",
            text,
            flags=re.IGNORECASE,
        )
        # remove extra spaces
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def _clean_discounted_product_price(price_: str | int | float) -> str:
        if isinstance(price_, (int, float)):
            return str(price_)
        elif isinstance(price_, str):
            clean_text = re.sub(r"[^0-9.]|(\.(?!\d))", "", price_)
            if not clean_text or clean_text == ".":
                return "0"
            return clean_text
        raise ValueError

    @staticmethod
    def _create_discounted_product(
        discounted_product_uuid: UUID,
        retailer_uuid: UUID,
        real_price: float | str,
        discounted_price: float | str,
        name: str,
        created_at: datetime,
        url: str,
    ) -> DiscountedProduct:
        price_details = PriceDetails(
            real_price=Decimal(str(real_price)),
            discounted_price=Decimal(str(discounted_price)),
        )
        discounted_product = DiscountedProduct(
            price_details=price_details,
            name=name,
            created_at=created_at,
            category_uuid=None,
            retailer_uuid=retailer_uuid,
            discounted_product_uuid=discounted_product_uuid,
            url=url,
        )
        return discounted_product


class DiscountedProductDTOFromYRetailer(TypedDict):
    name: str
    real_price: str
    discounted_price: str
    url: str
