from pydantic import BaseModel


class CreateRetailerRequestBodyModel(BaseModel):
    name: str
    url: str
    phone_number: str
