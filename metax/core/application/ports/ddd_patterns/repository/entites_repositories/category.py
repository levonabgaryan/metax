from abc import ABC, abstractmethod

from metax.core.application.ports.ddd_patterns.repository.errors import EntityIsNotFoundError
from metax.core.domain.ddd_patterns.general_value_objects import UUIDValueObject
from metax.core.domain.entities.category.entity import Category


class CategoryRepository(ABC):
    async def get_by_uuid(self, uuid_: UUIDValueObject) -> Category:
        category = await self._get_by_uuid(uuid_=uuid_)
        if category is None:
            raise EntityIsNotFoundError(
                entity_name="category",
                searched_field_name="uuid",
                searched_field_value=str(uuid_.value),
            )
        return category

    async def get_by_name(self, name: str) -> Category:
        category = await self._get_by_name(name=name)
        if category is None:
            raise EntityIsNotFoundError(
                entity_name="category",
                searched_field_name="name",
                searched_field_value=name,
            )
        return category

    async def add(self, category: Category) -> None:
        await self._add(category)

    async def update(self, updated_category: Category) -> None:
        await self._update(updated_category=updated_category)

    @abstractmethod
    async def get_all(self) -> list[Category]:
        pass

    @abstractmethod
    async def _get_by_uuid(self, uuid_: UUIDValueObject) -> Category | None:
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
