"""Pydanja ``DANJAResource.ignore_included`` returns raw ``data`` instead of ``handler(...)``; fix via subclass."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Self, cast, override

from pydanja import DANJAResource
from pydantic import model_validator
from pydantic.functional_validators import ModelWrapValidatorHandler

HTTP_RESOURCES = {
    "categoryResource",
    "discountedProductResource",
    "retailerResource",
    "categoryHelperWordResource",
}


class MetaxDANJAResource[ResourceT](DANJAResource[ResourceT]):
    @classmethod
    @override
    def from_basemodel(
        cls, resource: ResourceT, resource_name: str | None = None, resource_id: str | None = None
    ) -> Self:
        return cast(
            Self, super().from_basemodel(resource=resource, resource_name=resource_name, resource_id=resource_id)
        )

    @model_validator(mode="wrap")
    @override
    @classmethod
    def ignore_included(cls, data: Any, handler: ModelWrapValidatorHandler[Self]) -> Self:
        data_copy = deepcopy(data)

        # Exclude included resource types
        if hasattr(data_copy, "included"):
            del data_copy.included

        return handler(data_copy)

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
