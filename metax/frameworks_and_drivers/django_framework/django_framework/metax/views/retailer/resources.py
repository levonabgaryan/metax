from datetime import datetime
from typing import Annotated, Any, Self, override
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic.json_schema import SkipJsonSchema

from metax.frameworks_and_drivers.pydanja_.pydanja_resource import (
    RESOURCE_TYPE_RETAILER,
    MetaxDANJAResource,
    MetaxDANJAResourceList,
)


class RetailerResource(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"resource_name": RESOURCE_TYPE_RETAILER},
        populate_by_name=True,
        alias_generator=to_camel,
    )
    retailer_uuid: Annotated[
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
    home_page_url: str
    phone_number: str


class __RetailerPostRequestResource(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"resource_name": RESOURCE_TYPE_RETAILER},
        populate_by_name=True,
        alias_generator=to_camel,
    )
    retailer_uuid: Annotated[
        UUID | None,
        SkipJsonSchema(),
        Field(
            default=None,
            json_schema_extra={"resource_id": True},
            exclude=True,
        ),
    ]
    name: str
    home_page_url: str
    phone_number: str


class __RetailerPatchRequestResource(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"resource_name": RESOURCE_TYPE_RETAILER},
        populate_by_name=True,
        alias_generator=to_camel,
    )
    retailer_uuid: Annotated[
        UUID | None,
        SkipJsonSchema(),
        Field(
            default=None,
            json_schema_extra={"resource_id": True},
            exclude=True,
        ),
    ]
    name: str | None = None
    home_page_url: str | None = None
    phone_number: str | None = None


class RetailerPostRequestBody(MetaxDANJAResource[__RetailerPostRequestResource]):
    pass


class RetailerPatchRequestBody(MetaxDANJAResource[__RetailerPatchRequestResource]):
    pass


class RetailerResponseBody(MetaxDANJAResource[RetailerResource]):
    @classmethod
    @override
    def from_basemodel(
        cls, resource: RetailerResource, resource_name: str | None = None, resource_id: str | None = None
    ) -> Self:
        return super().from_basemodel(resource=resource, resource_name=resource_name, resource_id=resource_id)


class RetailerListResponseBody(MetaxDANJAResourceList[RetailerResource]):
    @classmethod
    @override
    def from_basemodel_list(
        cls, resources: list[RetailerResource], resource_name: str | None = None, resource_id: str | None = None
    ) -> Self:
        return super().from_basemodel_list(
            resources=resources, resource_name=resource_name, resource_id=resource_id
        )


_RETAILER_POST_AND_PATCH_OPENAPI_EXAMPLE: dict[str, Any] = {
    "data": {
        "type": RESOURCE_TYPE_RETAILER,
        "attributes": {
            "name": "yerevan-city",
            "homePageUrl": "https://example.com",
            "phoneNumber": "+37494646474",
        },
    },
}
