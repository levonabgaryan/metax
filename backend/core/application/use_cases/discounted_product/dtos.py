from dataclasses import dataclass, field
from uuid import UUID

from backend.core.application.patterns.use_case_abc import RequestDTO, ResponseDTO
from backend.core.domain.entities.discounted_product_entity.discounted_product import PriceDetails


@dataclass(frozen=True)
class CollectDiscountedProductsFromRetailerRequest(RequestDTO):
    retailer_url: str


@dataclass(frozen=True)
class DiscountedEntityBaseResponse(ResponseDTO):
    discounted_product_uuid: UUID
    retailer_name: str
    name: str
    price_details: PriceDetails
    url: str | None = field(default=None)
    category_name: str | None = field(default=None)
