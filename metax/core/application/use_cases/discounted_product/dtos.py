from dataclasses import dataclass
from datetime import datetime

from metax.core.application.use_cases.base_use_case import RequestDTO, ResponseDTO


@dataclass(frozen=True)
class CollectDiscountedProductsRequest(RequestDTO):
    started_time: datetime


@dataclass(frozen=True)
class CollectDiscountedProductsResponse(ResponseDTO):
    added_count: int
