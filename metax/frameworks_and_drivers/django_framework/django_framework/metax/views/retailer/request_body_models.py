import msgspec


class CreateRetailerRequestBodyModel(msgspec.Struct):
    name: str
    url: str
    phone_number: str
