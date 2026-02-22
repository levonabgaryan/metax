from __future__ import annotations
import re
from abc import ABC, abstractmethod
from typing import AsyncIterator, TypedDict

from discount_service.core.domain.entities.discounted_product_entity.discounted_product import DiscountedProduct


class ScrapperContext:
    def __init__(self, scrapper_strategy: ScrapperStrategy) -> None:
        self._scrapper_strategy = scrapper_strategy

    def get_scrapper_strategy(self) -> ScrapperStrategy:
        return self._scrapper_strategy

    def set_scrapper_strategy(self, scrapper_strategy: ScrapperStrategy) -> None:
        self._scrapper_strategy = scrapper_strategy


class ScrapperStrategy(ABC):
    def __init__(self, data_source_url: str) -> None:
        self._data_source_url = data_source_url

    @abstractmethod
    def fetch(self) -> AsyncIterator[DiscountedProduct]:
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


class DiscountedProductDTOFromYRetailer(TypedDict):
    name: str
    real_price: str
    discounted_price: str
    url: str
