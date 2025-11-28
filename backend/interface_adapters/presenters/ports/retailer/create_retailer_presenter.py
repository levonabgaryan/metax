from abc import ABC, abstractmethod
from typing import TypeVar

from backend.core.application.patterns.result_type import Error
from backend.core.application.use_cases.retailer.dtos import CreateRetailerResponse
from backend.interface_adapters.error_view_model import ErrorViewModel

CreateRetailerViewModel = TypeVar("CreateRetailerViewModel")


class ICreateRetailerPresenter[CreateRetailerViewModel](ABC):
    @abstractmethod
    def present_view_model(self, response: CreateRetailerResponse) -> CreateRetailerViewModel:
        pass

    @abstractmethod
    def present_error_view_model(self, error: Error) -> ErrorViewModel:
        pass
