from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import datetime

from metax.core.domain.entities.discounted_product.aggregate_root_entity import DiscountedProduct
from metax.core.domain.entities.retailer.aggregate_root_entity import Retailer


class DiscountedProductCollectorService(ABC):
    def __init__(self, retailer: Retailer) -> None:
        self._retailer = retailer

    @abstractmethod
    def collect(self, start_date_of_collecting: datetime) -> AsyncIterator[DiscountedProduct]:
        pass
