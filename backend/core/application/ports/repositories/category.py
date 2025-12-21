from abc import ABC, abstractmethod
from uuid import UUID
from dataclasses import dataclass, field

from backend.core.application.ports.repositories.errors.error_codes import RepositoriesErrorCodes
from backend.core.application.ports.repositories.errors.errors import EntityIsNotFoundError
from backend.core.domain.entities.category_entity.category import Category


@dataclass(frozen=True)
class CategoryFieldsToUpdate:
    name: bool = field(default=False)


class CategoryRepository(ABC):
    def __init__(self) -> None:
        self.seen: set[Category] = set()

    async def get_by_uuid(self, category_uuid: UUID) -> Category:
        category = await self._get_by_uuid(category_uuid=category_uuid)
        if category is None:
            raise EntityIsNotFoundError(
                entity_name="category",
                searched_field_name="uuid",
                searched_field_value=str(category_uuid),
                error_code=RepositoriesErrorCodes.CATEGORY_IS_NOT_FOUND,
            )
        self.seen.add(category)
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
        self.seen.add(category)
        return category

    async def add(self, category: Category) -> None:
        await self._add(category)
        self.seen.add(category)

    async def update(self, updated_category: Category, fields_to_update: CategoryFieldsToUpdate) -> None:
        await self._update(updated_category=updated_category, fields_to_update=fields_to_update)
        self.seen.add(updated_category)

    async def update_helper_words(self, updated_category: Category) -> None:
        await self._update_helper_words(updated_category=updated_category)
        self.seen.add(updated_category)

    @abstractmethod
    async def _get_by_uuid(self, category_uuid: UUID) -> Category | None:
        pass

    @abstractmethod
    async def _add(self, category: Category) -> None:
        pass

    @abstractmethod
    async def _get_by_name(self, category_name: str) -> Category | None:
        pass

    @abstractmethod
    async def _update(self, updated_category: Category, fields_to_update: CategoryFieldsToUpdate) -> None:
        pass

    @abstractmethod
    async def _update_helper_words(self, updated_category: Category) -> None:
        pass
