from typing import Required, NotRequired

from backend.interface_adapters.view_models.base_view_model import BaseViewModel


class RetailerBaseViewModel(BaseViewModel):
    retailer_uuid: Required[str]
    name: Required[str]
    url: NotRequired[str]
    phone_number: NotRequired[str]
