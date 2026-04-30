from abc import ABC, abstractmethod
from uuid import UUID

from metax.core.application.ports.ddd_patterns.repository.errors import EntityIsNotFoundError
from metax.core.domain.entities.category.aggregate_root_entity import Category

type TotalCount = int


class CategoryRepository(ABC):
    async def get_by_uuid(self, uuid_: UUID) -> Category:
        category = await self._get_by_uuid(uuid_=uuid_)
        if category is None:
            raise EntityIsNotFoundError(
                entity_type="category",
                searched_field_name="uuid",
                searched_field_value=str(uuid_),
            )
        return category

    async def get_by_name(self, name: str) -> Category:
        category = await self._get_by_name(name=name)
        if category is None:
            raise EntityIsNotFoundError(
                entity_type="category",
                searched_field_name="name",
                searched_field_value=name,
            )
        return category

    async def add(self, category: Category) -> None:
        await self._add(category)

    async def update(self, updated_category: Category) -> None:
        await self._update(updated_category=updated_category)

    async def delete_by_uuid(self, uuid_: UUID) -> None:
        deleted_uuid = await self._delete_by_uuid_and_return_uuid(uuid_)
        if deleted_uuid is None:
            raise EntityIsNotFoundError(
                entity_type="category",
                searched_field_name="uuid",
                searched_field_value=str(uuid_),
            )

    @abstractmethod
    async def all(self) -> list[Category]:
        pass

    @abstractmethod
    async def list_paginated_and_total_count(self, limit: int, offset: int) -> tuple[TotalCount, list[Category]]:
        """Returns list of category by params, and whole count of categories in the repository."""

    async def get_by_helper_word_uuid(self, helper_word_uuid: UUID) -> Category:
        category = await self._get_by_helper_word_uuid(helper_word_uuid=helper_word_uuid)
        if category is None:
            raise EntityIsNotFoundError(
                entity_type="category",
                searched_field_name="helper_word_uuid",
                searched_field_value=str(helper_word_uuid),
            )
        return category

    @abstractmethod
    async def _get_by_helper_word_uuid(self, helper_word_uuid: UUID) -> Category | None:
        pass

    @abstractmethod
    async def _delete_by_uuid_and_return_uuid(self, uuid_: UUID) -> UUID | None:
        pass

    @abstractmethod
    async def _get_by_uuid(self, uuid_: UUID) -> Category | None:
        pass

    @abstractmethod
    async def _add(self, category: Category) -> None:
        pass

    @abstractmethod
    async def _get_by_name(self, name: str) -> Category | None:
        pass

    @abstractmethod
    async def _update(self, updated_category: Category) -> None:
        pass
