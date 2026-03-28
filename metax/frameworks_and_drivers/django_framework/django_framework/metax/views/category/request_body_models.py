import msgspec


class CreateCategoryModel(msgspec.Struct):
    category_name: str
    helper_words: list[str]
