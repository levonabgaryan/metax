from abc import ABC, abstractmethod
from datetime import datetime
from typing import AsyncIterator
import re

from discount_service.core.domain.entities.discounted_product_entity.discounted_product import (
    DiscountedProduct,
)


class DiscountedProductFactory(ABC):
    @abstractmethod
    def create_many_from_retailer(
        self, started_time: datetime, batch_size: int = 500
    ) -> AsyncIterator[list[DiscountedProduct]]:
        # https://mypy.readthedocs.io/en/stable/more_types.html#asynchronous-iterators
        pass

    @staticmethod
    def clean_text_and_split(text: str) -> list[str]:
        # Strips text of unnecessary characters and returns a list of words.
        # Only Latin letters and numbers are retained.
        text = text.lower()
        text = re.sub(r"[^a-z0-9а-яёա-ֆ]+", " ", text, flags=re.IGNORECASE)
        words_ = [word for word in text.lower().split() if word]
        return words_
