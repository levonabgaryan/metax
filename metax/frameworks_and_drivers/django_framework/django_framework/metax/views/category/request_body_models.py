import msgspec


class CreateCategoryRequestBodyModel(msgspec.Struct):
    category_name: str
    helper_words: list[str]
