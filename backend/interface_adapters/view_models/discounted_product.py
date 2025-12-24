from typing import NotRequired, Required

from backend.interface_adapters.view_models.base_view_model import BaseViewModel


class DiscountedProductBaseViewModel(BaseViewModel):
    discounted_product_uuid: Required[str]
    category_name: Required[str]
    retailer_name: Required[str]
    real_price: Required[str]
    discounted_price: Required[str]
    name: Required[str]
    url: NotRequired[str]
