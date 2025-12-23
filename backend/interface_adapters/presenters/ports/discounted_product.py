from abc import ABC, abstractmethod
from typing import Any, AsyncIterator

from backend.core.domain.entities.discounted_product_entity.discounted_product import DiscountedProduct
from backend.interface_adapters.patterns.operation_result import ErrorViewModel
from backend.interface_adapters.view_models.retailer import RetailerBaseViewModel


class IDiscountedProductPresenter(ABC):
    @abstractmethod
    def present(self, discounted_product: DiscountedProduct) -> RetailerBaseViewModel:
        pass

    @abstractmethod
    def present_error(self, message: str, error_code: str, details: dict[str, Any]) -> ErrorViewModel:
        pass

    @abstractmethod
    async def present_many(self, discounted_products: AsyncIterator[DiscountedProduct]) -> AsyncIterator[RetailerBaseViewModel]:
        pass
