from uuid import UUID

from app.core.domain.ddd_patterns import AggregateRootEntity


class Category(AggregateRootEntity):
    def __init__(self, category_uuid: UUID, name: str) -> None:
        super().__init__(_uuid=category_uuid)
        self.__name = name
