from abc import ABC, abstractmethod
from typing import TypeVar

from backend.core.application.patterns.empty_dto import EmptyResponse
from backend.core.application.patterns.result_type import Error
from backend.interface_adapters.error_view_model import ErrorViewModel

DeleteCategoryHelperWordsViewModel = TypeVar("DeleteCategoryHelperWordsViewModel")


class IDeleteCategoryHelperWordsPresenter[DeleteCategoryHelperWordsViewModel](ABC):
    @abstractmethod
    def present_view_model(self, response: EmptyResponse) -> DeleteCategoryHelperWordsViewModel:
        pass

    @abstractmethod
    def present_error_view_model(self, error: Error) -> ErrorViewModel:
        pass
