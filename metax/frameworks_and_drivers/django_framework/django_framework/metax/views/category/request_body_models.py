from uuid import UUID

from pydantic import BaseModel


class CategoryPostRequestBody(BaseModel):
    category_name: str
    helper_words: list[str]


class CategoryPostResponseBodyModel(BaseModel):
    category_uuid: UUID
