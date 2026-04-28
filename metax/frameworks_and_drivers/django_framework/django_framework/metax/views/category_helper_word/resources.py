from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic.json_schema import SkipJsonSchema

from metax.frameworks_and_drivers.pydanja_.pydanja_resource import (
    RESOURCE_TYPE_CATEGORY_HELPER_WORD,
    MetaxDANJAResource,
    MetaxDANJAResourceList,
)


class CategoryHelperWordResource(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"resource_name": RESOURCE_TYPE_CATEGORY_HELPER_WORD},
        populate_by_name=True,
        alias_generator=to_camel,
    )
    helper_word_uuid: Annotated[
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
    helper_word: str


class __CategoryHelperWordPostRequestResource(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"resource_name": RESOURCE_TYPE_CATEGORY_HELPER_WORD},
        populate_by_name=True,
        alias_generator=to_camel,
    )
    helper_word_uuid: Annotated[
        UUID | None,
        SkipJsonSchema(),
        Field(
            default=None,
            json_schema_extra={"resource_id": True},
            exclude=True,
        ),
    ]
    helper_word: str


class __CategoryHelperWordPatchRequestResource(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"resource_name": RESOURCE_TYPE_CATEGORY_HELPER_WORD},
        populate_by_name=True,
        alias_generator=to_camel,
    )
    helper_word_uuid: Annotated[
        UUID | None,
        SkipJsonSchema(),
        Field(
            default=None,
            json_schema_extra={"resource_id": True},
            exclude=True,
        ),
    ]

    helper_word: str | None = None


class CategoryHelperWordPostRequestBody(MetaxDANJAResource[__CategoryHelperWordPostRequestResource]):
    pass


class CategoryHelperWordPatchRequestBody(MetaxDANJAResource[__CategoryHelperWordPatchRequestResource]):
    pass


class CategoryHelperWordResponseBody(MetaxDANJAResource[CategoryHelperWordResource]):
    pass


class CategoryHelperWordListResponseBody(MetaxDANJAResourceList[CategoryHelperWordResponseBody]):
    pass


_CATEGORY_HELPER_WORD_POST_AND_PATCH_OPENAPI_EXAMPLE: dict[str, Any] = {
    "data": {
        "type": "categoryHelperWord",
        "attributes": {"helperWord": "Marshall Emberton III"},
        "relationships": {
            "category": {"data": {"type": "category", "id": "019dd091-7968-75a8-ba01-2db4f33aa63f"}}
        },
    }
}
