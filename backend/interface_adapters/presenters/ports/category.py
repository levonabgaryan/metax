from abc import ABC, abstractmethod
from typing import Any

from backend.core.domain.entities.category_entity.category import Category
from backend.interface_adapters.patterns.operation_result import ErrorViewModel
from backend.interface_adapters.view_models.category import CategoryBaseViewModel


class ICategoryPresenter(ABC):
    @abstractmethod
    def present(self, category: Category) -> CategoryBaseViewModel:
        pass

    @abstractmethod
    def present_error(self, message: str, error_code: str, details: dict[str, Any]) -> ErrorViewModel:
        pass