from dataclasses import dataclass
from datetime import datetime

from discount_service.core.application.patterns.use_case_abc import RequestDTO, ResponseDTO


@dataclass(frozen=True)
class CollectDiscountedProductsRequest(RequestDTO):
    started_time: datetime


@dataclass(frozen=True)
class CollectDiscountedProductsResponse(ResponseDTO):
    added_count: int
