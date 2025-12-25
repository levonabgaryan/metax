from typing import Annotated
from uuid import UUID

from pydantic import Field, PlainSerializer

from backend.core.application.use_cases.category.dtos import CategoryEntityDTO
from ..base_shcema import BaseSchema
from backend.interface_adapters.view_models.category import CategoryEntityViewModel


class CategoryEntityViewModelSchema(BaseSchema):
    category_uuid: Annotated[UUID, PlainSerializer(lambda v: str(v), return_type=str)]
    name: Annotated[str, Field(min_length=1)]
    helper_words: Annotated[frozenset[str], PlainSerializer(lambda v: list(v), return_type=list[str])]

    @classmethod
    def to_view_model(cls, response_dto: CategoryEntityDTO) -> CategoryEntityViewModel:
        validated_view_model = cls.model_validate(response_dto).model_dump()
        return CategoryEntityViewModel(
            category_uuid=validated_view_model["category_uuid"],
            name=validated_view_model["name"],
            helper_words=validated_view_model["helper_words"],
        )
