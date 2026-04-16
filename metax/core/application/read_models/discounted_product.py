from typing import NotRequired, Required, TypedDict


class DiscountedProductReadModel(TypedDict):
    uuid_: NotRequired[str]
    name: Required[str]
    real_price: Required[float]
    discounted_price: Required[float]
    category_uuid: NotRequired[str | None]
    category_name: NotRequired[str | None]
    retailer_uuid: Required[str]
    retailer_name: Required[str]
    url: NotRequired[str | None]
    created_at: Required[str]  # iso format
