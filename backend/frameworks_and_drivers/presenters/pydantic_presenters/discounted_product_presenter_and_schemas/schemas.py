from typing import Optional, Annotated
from uuid import UUID

from pydantic import PlainSerializer

from backend.core.application.use_cases.discounted_product.dtos import DiscountedProductEntityDTO
from backend.core.domain.entities.discounted_product_entity.discounted_product import PriceDetails
from backend.interface_adapters.view_models.discounted_product import DiscountedProductEntityViewModel
from ..base_shcema import BaseSchema


class DiscountedProductEntityViewModelSchema(BaseSchema):
    discounted_product_uuid: Annotated[UUID, PlainSerializer(lambda v: str(v), return_type=str)]
    retailer_name: str
    name: str
    price_details: PriceDetails
    url: Optional[str]
    category_name: Optional[str]

    @classmethod
    def to_view_model(cls, response_dto: DiscountedProductEntityDTO) -> DiscountedProductEntityViewModel:
        validated_data = cls.model_validate(response_dto).model_dump()
        return DiscountedProductEntityViewModel(
            discounted_product_uuid=validated_data["discounted_product_uuid"],
            category_name=validated_data.get("category_name"),
            retailer_name=validated_data["retailer_name"],
            real_price=validated_data["real_price"],
            discounted_price=validated_data["discounted_price"],
            name=validated_data["name"],
            url=validated_data.get("url"),
        )
