from abc import ABC, abstractmethod
from uuid import UUID

from backend.core.domain.entities.category_entity.category import Category


class ICategoryRepository(ABC):
    @abstractmethod
    async def get_by_uuid(self, category_uuid: UUID) -> Category:
        pass

    @abstractmethod
    async def save(self, category: Category) -> None:
        pass

    @abstractmethod
    async def get_by_name(self, category_name: str) -> Category:
        pass
