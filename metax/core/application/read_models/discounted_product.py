from typing import NotRequired, Required, TypedDict


class DiscountedProductReadModel(TypedDict):
    uuid_: Required[str]
    name: Required[str]
    real_price: Required[float]
    discounted_price: Required[float]
    category_uuid: NotRequired[str]
    category_name: NotRequired[str]
    retailer_uuid: Required[str]
    retailer_name: Required[str]
    url: Required[str]
    created_at: Required[str]  # iso format
