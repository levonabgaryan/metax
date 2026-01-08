from dataclasses import dataclass
from datetime import datetime

from discount_service.core.application.patterns.use_case_abc import RequestDTO, ResponseDTO


@dataclass(frozen=True)
class CollectDiscountedProductsFromRetailerRequest(RequestDTO):
    retailer_url: str
    started_time: datetime


@dataclass(frozen=True)
class CollectDiscountedProductsFromRetailerResponse(ResponseDTO):
    added_count: int
