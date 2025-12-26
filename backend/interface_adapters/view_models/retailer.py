from typing import TypedDict, Required, NotRequired


class RetailerViewModel(TypedDict):
    retailer_uuid: Required[str]
    name: Required[str]
    url: NotRequired[str]
    phone_number: NotRequired[str]
