from typing import TypedDict, Required


class CategoryBaseViewModel(TypedDict):
    category_uuid: Required[str]
    name: Required[str]
    helper_words: Required[list[str]]
