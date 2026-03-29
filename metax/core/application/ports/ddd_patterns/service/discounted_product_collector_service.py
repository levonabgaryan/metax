from abc import ABC, abstractmethod
from datetime import datetime
from typing import AsyncIterator

from metax.core.domain.entities.discounted_product.entity import DiscountedProduct
from metax.core.domain.entities.retailer.entity import Retailer


class DiscountedProductCollectorService(ABC):
    def __init__(self, retailer: Retailer) -> None:
        self._retailer = retailer

    @abstractmethod
    def collect(self, start_date_of_collecting: datetime) -> AsyncIterator[DiscountedProduct]:
        pass
