from uuid import UUID

import msgspec


class CreateCategoryResponseBodyModel(msgspec.Struct):
    category_uuid: UUID
