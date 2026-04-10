from abc import ABC, abstractmethod
from uuid import UUID

from metax.core.application.ports.ddd_patterns.repository.errors.error_codes import RepositoriesErrorCodes
from metax.core.application.ports.ddd_patterns.repository.errors.errors import EntityIsNotFoundError
from metax.core.domain.entities.category.entity import Category


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

    async def add(self, category: Category) -> None:
        await self._add(category)

    async def update(self, updated_category: Category) -> None:
        await self._update(updated_category=updated_category)

    async def update_helper_words(self, updated_category: Category) -> None:
        await self._update_helper_words(updated_category=updated_category)

    async def get_by_helper_words_in_words(self, words: list[str]) -> Category:
        words = [w.lower() for w in words]
        category = await self._get_by_helper_words_in_words(words=words)
        if category is None:
            raise EntityIsNotFoundError(
                entity_name="category",
                searched_field_name="helper_words",
                searched_field_value=f"{words}",
                error_code=RepositoriesErrorCodes.CATEGORY_IS_NOT_FOUND,
            )
        return category

    @abstractmethod
    async def get_all(self) -> list[Category]:
        pass

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
    async def _update(self, updated_category: Category) -> None:
        pass

    @abstractmethod
    async def _update_helper_words(self, updated_category: Category) -> None:
        pass

    @abstractmethod
    async def _get_by_helper_words_in_words(self, words: list[str]) -> Category | None:
        pass
