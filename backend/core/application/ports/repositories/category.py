from abc import ABC, abstractmethod
from uuid import UUID

from backend.core.application.ports.repositories.errors.error_codes import RepositoriesErrorCodes
from backend.core.application.ports.repositories.errors.errors import EntityIsNotFoundError
from backend.core.domain.entities.category_entity.category import Category


class CategoryRepository(ABC):
    async def get_by_uuid(self, category_uuid: UUID) -> Category:
        category = await self._get_by_uuid(category_uuid=category_uuid)
        if category is None:
            raise EntityIsNotFoundError(
                entity_name="category",
                searched_field_name="uuid",
                searched_field_value=str(category_uuid),
                error_code=RepositoriesErrorCodes.CATEGORY_IS_NOT_FOUND,
            )
        return category

    async def get_by_name(self, category_name: str) -> Category:
        category = await self._get_by_name(category_name=category_name)
        if category is None:
            raise EntityIsNotFoundError(
                entity_name="category",
                searched_field_name="name",
                searched_field_value=category_name,
                error_code=RepositoriesErrorCodes.CATEGORY_IS_NOT_FOUND,
            )
        return category

    @abstractmethod
    async def _get_by_uuid(self, category_uuid: UUID) -> Category | None:
        pass

    @abstractmethod
    async def save(self, category: Category) -> None:
        pass

    @abstractmethod
    async def _get_by_name(self, category_name: str) -> Category | None:
        pass
