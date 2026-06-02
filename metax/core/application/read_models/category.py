from typing import Required, TypedDict


class CategoryReadModel(TypedDict):
    uuid_: Required[str]
    created_at: Required[str]
    updated_at: Required[str]
    name: Required[str]
    name_hy: Required[str]
    name_ru: Required[str]
