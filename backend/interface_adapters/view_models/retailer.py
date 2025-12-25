from typing import Required, NotRequired, Optional

from backend.interface_adapters.view_models.base_view_model import BaseViewModel


class RetailerEntityViewModel(BaseViewModel):
    retailer_uuid: Required[str]
    name: Required[str]
    url: NotRequired[Optional[str]]
    phone_number: NotRequired[Optional[str]]
