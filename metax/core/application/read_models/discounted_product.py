from typing import NotRequired, Required, TypedDict


class DiscountedProductCategoryReadModel(TypedDict):
    """Category fragment embedded in the discounted product read model."""

    uuid_: Required[str]
    created_at: Required[str]
    updated_at: Required[str]
    name: Required[str]
    name_hy: Required[str]
    name_ru: Required[str]


class DiscountedProductRetailerReadModel(TypedDict):
    """Retailer fragment embedded in the discounted product read model."""

    uuid_: Required[str]
    created_at: Required[str]
    updated_at: Required[str]
    name: Required[str]
    home_page_url: Required[str]
    phone_number: Required[str]


class DiscountedProductReadModel(TypedDict):
    """Projection for search; nested ``category`` / ``retailer`` are read live via SQL joins."""

    uuid_: Required[str]
    created_at: Required[str]
    updated_at: Required[str]
    name: Required[str]
    real_price: Required[float]
    discounted_price: Required[float]
    url: Required[str]
    retailer: Required[DiscountedProductRetailerReadModel]
    category: NotRequired[DiscountedProductCategoryReadModel]
    image_url: NotRequired[str]
    # How confident the classifier is that the product belongs to its category (0..1, higher =
    # surer); present only when browsing a category.
    category_confidence: NotRequired[float]
    # How closely the product matched a name/phonetic search query (0..1, higher = closer);
    # present only on name searches.
    match_confidence: NotRequired[float]
