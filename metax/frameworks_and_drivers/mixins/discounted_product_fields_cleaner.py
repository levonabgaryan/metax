import re
from typing import overload


class DiscountedProductFieldsCleanerMixin:
    @staticmethod
    def clean_discounted_product_name(text: str) -> str:
        """Normalize only whitespace, keeping the source name's original case and punctuation.

        The name is shown to users verbatim, so we keep it faithful to the retailer's web page.
        Case- and punctuation-insensitive matching is handled at search time (semantic embedding
        plus an ILIKE boost), not here, so no lowercasing or symbol stripping is needed.

        Returns:
            The name with surrounding whitespace trimmed and internal whitespace runs collapsed.
        """
        return re.sub(r"\s+", " ", text).strip()

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
    def clean_discounted_product_price(price_: str | float) -> str:
        if isinstance(price_, (int, float)):
            return str(price_)
        if isinstance(price_, str):
            clean_text = re.sub(r"[^0-9.]|(\.(?!\d))", "", price_)
            if not clean_text or clean_text == ".":
                return "0"
            return clean_text
        raise ValueError
