from abc import ABC, abstractmethod
from typing import TypeVar

from backend.core.application.patterns.result_type import Result
from backend.core.application.use_cases.category.dtos import CreateCategoryResponse
from backend.interface_adapters.error_view_model import ErrorViewModel

CreateCategoryViewModel = TypeVar("CreateCategoryViewModel")


class ICreateCategoryPresenter[CreateCategoryViewModel](ABC):
    @staticmethod
    @abstractmethod
    def present(response: Result[CreateCategoryResponse]) -> CreateCategoryViewModel | ErrorViewModel:
        pass
