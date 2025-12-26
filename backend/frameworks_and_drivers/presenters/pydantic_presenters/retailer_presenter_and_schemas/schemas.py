from typing import Annotated, Optional
from uuid import UUID

from pydantic import PlainSerializer, Field

from backend.core.application.use_cases.retailer.dtos import RetailerEntityResponseDTO
from backend.interface_adapters.view_models.retailer import RetailerEntityViewModel
from ..base_shcema import BaseSchema


class RetailerEntityViewModelSchema(BaseSchema):
    retailer_uuid: Annotated[UUID, PlainSerializer(lambda v: str(v), return_type=str)]
    name: Annotated[str, Field(min_length=1)]
    url: Optional[str]
    phone_number: Optional[str]

    @classmethod
    def to_view_model(cls, response_dto: RetailerEntityResponseDTO) -> RetailerEntityViewModel:
        validated_view_model = cls.model_validate(response_dto).model_dump()
        return RetailerEntityViewModel(
            retailer_uuid=validated_view_model["retailer_uuid"],
            name=validated_view_model["name"],
            url=validated_view_model.get("url"),
            phone_number=validated_view_model.get("phone_number"),
        )
