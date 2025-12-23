from typing import TypedDict, NotRequired, Required


class DiscountedProductBaseViewModel(TypedDict):
    discounted_product_uuid: Required[str]
    category_name: Required[str]
    retailer_name: Required[str]
    real_price: Required[str]
    discounted_price: Required[str]
    name: Required[str]
    url: NotRequired[str]
