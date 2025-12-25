from typing import Required

from backend.interface_adapters.view_models.base_view_model import BaseViewModel


class CategoryEntityViewModel(BaseViewModel):
    category_uuid: Required[str]
    name: Required[str]
    helper_words: Required[list[str]]
