import re
from typing import overload


class DiscountedProductFieldsCleanerMixin:
    @staticmethod
    def clean_discounted_product_name(text: str) -> str:
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

    @overload
    @staticmethod
    def clean_discounted_product_price(price_: str) -> str: ...

    @overload
    @staticmethod
    def clean_discounted_product_price(price_: int) -> str: ...

    @overload
    @staticmethod
    def clean_discounted_product_price(price_: float) -> str: ...

    @staticmethod
    def clean_discounted_product_price(price_: str | int | float) -> str:
        if isinstance(price_, (int, float)):
            return str(price_)
        elif isinstance(price_, str):
            clean_text = re.sub(r"[^0-9.]|(\.(?!\d))", "", price_)
            if not clean_text or clean_text == ".":
                return "0"
            return clean_text
        raise ValueError
