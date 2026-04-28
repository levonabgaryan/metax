from datetime import datetime
from typing import Annotated, Any, Self, override
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic.json_schema import SkipJsonSchema

from metax.frameworks_and_drivers.pydanja_.pydanja_resource import (
    RESOURCE_TYPE_CATEGORY,
    MetaxDANJAResource,
    MetaxDANJAResourceList,
)


class CategoryResource(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"resource_name": RESOURCE_TYPE_CATEGORY},
        populate_by_name=True,
        alias_generator=to_camel,
    )
    category_uuid: Annotated[
        UUID | None,
        SkipJsonSchema(),
        Field(
            default=None,
            json_schema_extra={"resource_id": True},
            exclude=True,
        ),
    ]
    created_at: datetime
    updated_at: datetime
    name: str


class __CategoryPostRequestResource(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"resource_name": RESOURCE_TYPE_CATEGORY},
        populate_by_name=True,
        alias_generator=to_camel,
    )
    category_uuid: Annotated[
        UUID | None,
        SkipJsonSchema(),
        Field(
            default=None,
            json_schema_extra={"resource_id": True},
            exclude=True,
        ),
    ]
    name: str


class __CategoryPatchRequestResource(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"resource_name": RESOURCE_TYPE_CATEGORY},
        populate_by_name=True,
        alias_generator=to_camel,
    )
    category_uuid: Annotated[
        UUID | None,
        SkipJsonSchema(),
        Field(
            default=None,
            json_schema_extra={"resource_id": True},
            exclude=True,
        ),
    ]
    name: str | None = None


class CategoryPostRequestBody(MetaxDANJAResource[__CategoryPostRequestResource]):
    pass


class CategoryPatchRequestBody(MetaxDANJAResource[__CategoryPatchRequestResource]):
    pass


class CategoryResponseBody(MetaxDANJAResource[CategoryResource]):
    @classmethod
    @override
    def from_basemodel(
        cls, resource: CategoryResource, resource_name: str | None = None, resource_id: str | None = None
    ) -> Self:
        return super().from_basemodel(resource=resource, resource_name=resource_name, resource_id=resource_id)


class CategoryListResponseBody(MetaxDANJAResourceList[CategoryResource]):
    @classmethod
    @override
    def from_basemodel_list(
        cls, resources: list[CategoryResource], resource_name: str | None = None, resource_id: str | None = None
    ) -> Self:
        return super().from_basemodel_list(
            resources=resources, resource_name=resource_name, resource_id=resource_id
        )


_CATEGORY_POST_AND_PATCH_OPENAPI_EXAMPLE: dict[str, Any] = {
    "data": {
        "type": RESOURCE_TYPE_CATEGORY,
        "attributes": {
            "name": "Electronics",
        },
    },
}
