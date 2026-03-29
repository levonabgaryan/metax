from uuid import UUID

import msgspec


class CreateRetailerResponseBodyModel(msgspec.Struct):
    retailer_uuid: UUID
