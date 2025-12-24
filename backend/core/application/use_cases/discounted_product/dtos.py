from dataclasses import dataclass

from backend.core.application.patterns.use_case_abc import RequestDTO


@dataclass(frozen=True)
class CollectDiscountedProductsFromRetailerRequest(RequestDTO):
    retailer_url: str
