from uuid import UUID

from pydantic import BaseModel


class CreateRetailerResponseBodyModel(BaseModel):
    retailer_uuid: UUID
