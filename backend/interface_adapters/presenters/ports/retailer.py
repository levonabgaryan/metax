from abc import ABC, abstractmethod
from typing import Any

from backend.core.domain.entities.retailer_entity.retailer import Retailer
from backend.interface_adapters.patterns.operation_result import ErrorViewModel
from backend.interface_adapters.view_models.retailer import RetailerBaseViewModel


class IRetailerPresenter(ABC):
    @abstractmethod
    def present(self, retailer: Retailer) -> RetailerBaseViewModel:
        pass
    @abstractmethod
    def present_error(self, message: str, error_code: str, details: dict[str, Any]) -> ErrorViewModel:
        pass