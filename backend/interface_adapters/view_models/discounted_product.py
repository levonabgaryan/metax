from typing import TypedDict, Required, NotRequired


class DiscountedProductViewModel(TypedDict):
    discounted_product_uuid: Required[str]
    category_name: NotRequired[str]
    retailer_name: Required[str]
    real_price: Required[str]
    discounted_price: Required[str]
    name: Required[str]
    url: NotRequired[str]
