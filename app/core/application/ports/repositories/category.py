from abc import ABC, abstractmethod
from uuid import UUID

from app.core.domain.entities.category_entity.category import Category

class CategoryRepository(ABC):
    @abstractmethod
    def get_by_uuid(self, category_uuid: UUID) -> Category:
        pass

    @abstractmethod
    def add(self, category: Category) -> None:
        pass
