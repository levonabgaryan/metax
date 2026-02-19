import re
from abc import ABC, abstractmethod
from typing import AsyncIterator, TypedDict


class ScrapperAdapter(ABC):
    def __init__(self, data_source_url: str) -> None:
        self._data_source_url = data_source_url

    @abstractmethod
    def fetch(self) -> AsyncIterator[DiscountedProductDTOFromYRetailer]:
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
