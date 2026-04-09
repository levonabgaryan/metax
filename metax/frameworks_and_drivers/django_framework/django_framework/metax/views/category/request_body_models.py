from pydantic import BaseModel


class CreateCategoryRequestBodyModel(BaseModel):
    category_name: str
    helper_words: list[str]
