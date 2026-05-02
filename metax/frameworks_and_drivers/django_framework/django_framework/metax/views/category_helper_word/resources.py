from datetime import datetime
from typing import Annotated, Any, Self, cast, override
from uuid import UUID

from pydanja import DANJARelationship, DANJAResourceIdentifier
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel
from pydantic.json_schema import SkipJsonSchema

from metax.frameworks_and_drivers.pydanja_.pydanja_resource import (
    RESOURCE_TYPE_CATEGORY,
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
    helper_word_text: str


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
    helper_word_text: str


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

    helper_word_text: str | None = None


class CategoryHelperWordPostRequestBody(MetaxDANJAResource[__CategoryHelperWordPostRequestResource]):
    @property
    def category_identifier(self) -> DANJAResourceIdentifier:
        # Safe cast: validate_category_relationship guarantees this shape.
        relationships = cast(dict[str, DANJARelationship], self.data.relationships)
        category_relationship = relationships[RESOURCE_TYPE_CATEGORY]
        return cast(DANJAResourceIdentifier, category_relationship.data)

    @model_validator(mode="after")
    def validate_category_relationship(self) -> Self:
        relationships = self.data.relationships
        if relationships is None:
            msg = f"Relationship block is required (link to '{RESOURCE_TYPE_CATEGORY}')"
            raise ValueError(msg)

        category_relationship = relationships.get(RESOURCE_TYPE_CATEGORY)
        if category_relationship is None:
            msg = f"Relationship '{RESOURCE_TYPE_CATEGORY}' is required"
            raise ValueError(msg)

        relationship_data = category_relationship.data
        if relationship_data is None or isinstance(relationship_data, list):
            msg = f"Relationship '{RESOURCE_TYPE_CATEGORY}.data' must contain a single resource identifier"
            raise ValueError(msg)

        return self


class CategoryHelperWordPatchRequestBody(MetaxDANJAResource[__CategoryHelperWordPatchRequestResource]):
    @property
    def category_identifier(self) -> DANJAResourceIdentifier:
        # Safe cast: validate_category_relationship guarantees this shape.
        relationships = cast(dict[str, DANJARelationship], self.data.relationships)
        category_relationship = relationships[RESOURCE_TYPE_CATEGORY]
        return cast(DANJAResourceIdentifier, category_relationship.data)

    @property
    def helper_word_text(self) -> str:
        helper_word_text = self.data.attributes.helper_word_text
        if helper_word_text is None:
            msg = "Attribute 'helperWordText' is required"
            raise ValueError(msg)
        return helper_word_text

    @model_validator(mode="after")
    def validate_category_relationship(self) -> Self:
        relationships = self.data.relationships
        if relationships is None:
            msg = f"Relationship block is required (link to '{RESOURCE_TYPE_CATEGORY}')"
            raise ValueError(msg)

        category_relationship = relationships.get(RESOURCE_TYPE_CATEGORY)
        if category_relationship is None:
            msg = f"Relationship '{RESOURCE_TYPE_CATEGORY}' is required"
            raise ValueError(msg)

        relationship_data = category_relationship.data
        if relationship_data is None or isinstance(relationship_data, list):
            msg = f"Relationship '{RESOURCE_TYPE_CATEGORY}.data' must contain a single resource identifier"
            raise ValueError(msg)

        return self


class CategoryHelperWordResponseBody(MetaxDANJAResource[CategoryHelperWordResource]):
    @override
    @classmethod
    def from_basemodel(
        cls,
        resource: CategoryHelperWordResource,
        resource_name: str | None = None,
        resource_id: str | None = None,
    ) -> Self:
        return super().from_basemodel(resource=resource, resource_name=resource_name, resource_id=resource_id)


class CategoryHelperWordListResponseBody(MetaxDANJAResourceList[CategoryHelperWordResponseBody]):
    @classmethod
    @override
    def from_basemodel_list(
        cls,
        resources: list[CategoryHelperWordResponseBody],
        resource_name: str | None = None,
        resource_id: str | None = None,
    ) -> Self:
        return super().from_basemodel_list(
            resources=resources, resource_name=resource_name, resource_id=resource_id
        )


CATEGORY_HELPER_WORD_POST_AND_PATCH_OPENAPI_EXAMPLE: dict[str, Any] = {
    "data": {
        "type": "categoryHelperWord",
        "attributes": {"helperWordText": "Marshall Emberton III"},
        "relationships": {
            "category": {"data": {"type": "category", "id": "019dd091-7968-75a8-ba01-2db4f33aa63f"}}
        },
    }
}


class CategoryHelperWordPath(BaseModel):
    helper_word_path: UUID
