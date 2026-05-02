from typing import Required, TypedDict


class RetailerReadModel(TypedDict):
    uuid_: Required[str]
    created_at: Required[str]
    updated_at: Required[str]
    name: Required[str]
    home_page_url: Required[str]
    phone_number: Required[str]
