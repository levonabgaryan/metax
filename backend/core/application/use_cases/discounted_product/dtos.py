from dataclasses import dataclass


@dataclass(frozen=True)
class CollectDiscountedProductsFromRetailerRequest:
    retailer_url: str
