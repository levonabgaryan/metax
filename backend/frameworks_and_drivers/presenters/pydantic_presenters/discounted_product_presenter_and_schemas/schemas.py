from typing import Optional, Annotated
from uuid import UUID

from pydantic import PlainSerializer

from backend.core.application.use_cases.discounted_product.dtos import DiscountedProductEntityResponseDTO
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
    def to_view_model(cls, response_dto: DiscountedProductEntityResponseDTO) -> DiscountedProductEntityViewModel:
        validated_data = cls.model_validate(response_dto).model_dump()
        prices = validated_data["price_details"]
        real_price = str(prices["real_price"])
        discounted_price = str(prices["discounted_price"])

        return DiscountedProductEntityViewModel(
            discounted_product_uuid=validated_data["discounted_product_uuid"],
            category_name=validated_data.get("category_name"),
            retailer_name=validated_data["retailer_name"],
            real_price=real_price,
            discounted_price=discounted_price,
            name=validated_data["name"],
            url=validated_data.get("url"),
        )
