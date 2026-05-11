import datetime as dt
from dataclasses import dataclass

from metax.core.application.base_dtos.base_dtos import RequestDTO, ResponseDTO


@dataclass(frozen=True)
class CollectDiscountedProductsRequest(RequestDTO):
    start_date_of_collecting: dt.datetime


@dataclass(frozen=True)
class CollectDiscountedProductsResponse(ResponseDTO):
    added_count: int
