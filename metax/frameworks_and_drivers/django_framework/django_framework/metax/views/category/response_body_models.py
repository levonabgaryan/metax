from uuid import UUID

from pydantic import BaseModel


class CreateCategoryResponseBodyModel(BaseModel):
    category_uuid: UUID
