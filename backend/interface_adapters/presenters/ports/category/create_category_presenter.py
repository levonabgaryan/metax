from abc import ABC, abstractmethod
from typing import TypeVar

from backend.core.application.patterns.result_type import Error
from backend.core.application.use_cases.category.dtos import CreateCategoryResponse
from backend.interface_adapters.error_view_model import ErrorViewModel

CreateCategoryViewModel = TypeVar("CreateCategoryViewModel")


class ICreateCategoryPresenter[CreateCategoryViewModel](ABC):
    @abstractmethod
    def present_view_model(self, response: CreateCategoryResponse) -> CreateCategoryViewModel:
        pass

    @abstractmethod
    def present_error_view_model(self, error: Error) -> ErrorViewModel:
        pass
