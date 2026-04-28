"""Pydanja ``DANJAResource.ignore_included`` returns raw ``data`` instead of ``handler(...)``; fix via subclass."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Self, cast, override

from pydanja import DANJAResource, DANJAResourceList
from pydantic import BaseModel, model_validator
from pydantic.functional_validators import ModelWrapValidatorHandler

# JSON:API resource type strings — single source of truth
# for `data.type`, `relationships` keys, pydanja `resource_name`.
RESOURCE_TYPE_CATEGORY = "category"
RESOURCE_TYPE_DISCOUNTED_PRODUCT = "discountedProduct"
RESOURCE_TYPE_RETAILER = "retailer"
RESOURCE_TYPE_CATEGORY_HELPER_WORD = "categoryHelperWord"

HTTP_RESOURCES: frozenset[str] = frozenset({
    RESOURCE_TYPE_CATEGORY,
    RESOURCE_TYPE_DISCOUNTED_PRODUCT,
    RESOURCE_TYPE_RETAILER,
    RESOURCE_TYPE_CATEGORY_HELPER_WORD,
})


class MetaxDANJAResource[ResourceT](DANJAResource[ResourceT]):
    @classmethod
    @override
    def from_basemodel(
        cls, resource: ResourceT, resource_name: str | None = None, resource_id: str | None = None
    ) -> Self:
        if not resource_id:
            resource_id = cls.resolve_resource_id(resource)
        result = super().from_basemodel(resource=resource, resource_name=resource_name, resource_id=resource_id)

        # JSON:API: avoid duplicating the identifier
        # in attributes when `data.id` is set (see pydanja `from_basemodel`).
        # Keep `attributes` as ResourceT via model_construct — not a dict — so pydantic
        # serialization matches DANJASingleResource.
        if resource_id and result.data.id:
            attributes = result.data.attributes
            if isinstance(attributes, dict):
                attributes.pop(resource_id, None)
            elif isinstance(attributes, BaseModel):
                cls_type = type(attributes)
                result.data.attributes = cls_type.model_construct(
                    **attributes.model_dump(exclude={resource_id}),
                )

        return cast(Self, result)

    @model_validator(mode="wrap")
    @override
    @classmethod
    def ignore_included(cls, data: Any, handler: ModelWrapValidatorHandler[Self]) -> Self:
        data_copy = deepcopy(data)

        # Exclude included resource types
        if isinstance(data_copy, dict):
            data_copy.pop("included", None)
        elif hasattr(data_copy, "included"):
            del data_copy.included

        return handler(data_copy)

    @model_validator(mode="before")
    @classmethod
    def lift_root_relationships_into_data(cls, data: Any) -> Any:
        """JSON:API nests ``relationships`` inside ``data``; pydanja matches that shape.

        Clients (and some examples) send a top-level ``relationships`` sibling — accept it here.

        Returns:
            data : ``data``
        """
        if not isinstance(data, dict):
            return data
        inner = data.get("data")
        root_rels = data.get("relationships")
        if not isinstance(inner, dict) or root_rels is None:
            return data
        if inner.get("relationships") is not None:
            return data
        out = dict(data)
        out["data"] = {**inner, "relationships": root_rels}
        del out["relationships"]
        return out

    @model_validator(mode="before")
    @classmethod
    def validate_resource_type(cls, data: Any) -> Any:
        cls.__recursive_check(data)
        return data

    @classmethod
    def __recursive_check(cls, data: Any) -> None:
        if isinstance(data, dict):
            res_type = data.get("type")
            if res_type is not None and res_type not in HTTP_RESOURCES:
                msg = f"Unsupported resource type: {res_type}. Supported types: {list(HTTP_RESOURCES)}"
                raise ValueError(msg)

            for value in data.values():
                cls.__recursive_check(value)

        elif isinstance(data, list):
            for item in data:
                cls.__recursive_check(item)


class MetaxDANJAResourceList[ResourceT](DANJAResourceList[ResourceT]):
    @model_validator(mode="wrap")
    @override
    @classmethod
    def ignore_included(cls, data: Any, handler: ModelWrapValidatorHandler[Self]) -> Self:
        data_copy = deepcopy(data)

        # Exclude included resource types
        if hasattr(data_copy, "included"):
            del data_copy.included

        return handler(data_copy)

    @classmethod
    @override
    def from_basemodel_list(
        cls, resources: list[ResourceT], resource_name: str | None = None, resource_id: str | None = None
    ) -> Self:
        return cast(
            Self,
            super().from_basemodel_list(resources=resources, resource_name=resource_name, resource_id=resource_id),
        )
