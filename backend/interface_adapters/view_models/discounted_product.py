from typing import NotRequired, Required, Optional

from backend.interface_adapters.view_models.base_view_model import BaseViewModel


class DiscountedProductEntityViewModel(BaseViewModel):
    discounted_product_uuid: Required[str]
    category_name: NotRequired[Optional[str]]
    retailer_name: Required[str]
    real_price: Required[str]
    discounted_price: Required[str]
    name: Required[str]
    url: NotRequired[Optional[str]]
