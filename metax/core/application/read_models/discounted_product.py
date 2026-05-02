from typing import NotRequired, Required, TypedDict


class DiscountedProductCategoryReadModel(TypedDict):
    """Category fragment embedded in the discounted product read model."""

    uuid_: Required[str]
    created_at: Required[str]
    updated_at: Required[str]
    name: Required[str]


class DiscountedProductRetailerReadModel(TypedDict):
    """Retailer fragment embedded in the discounted product read model."""

    uuid_: Required[str]
    created_at: Required[str]
    updated_at: Required[str]
    name: Required[str]
    home_page_url: Required[str]
    phone_number: Required[str]


class DiscountedProductReadModel(TypedDict):
    """Projection for search; nested ``category`` / ``retailer`` match OpenSearch document fields."""

    uuid_: Required[str]
    created_at: Required[str]
    updated_at: Required[str]
    name: Required[str]
    real_price: Required[float]
    discounted_price: Required[float]
    url: Required[str]
    retailer: Required[DiscountedProductRetailerReadModel]
    category: NotRequired[DiscountedProductCategoryReadModel]
