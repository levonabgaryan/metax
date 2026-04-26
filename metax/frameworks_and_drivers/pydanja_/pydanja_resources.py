"""Pydanja ``DANJAResource.ignore_included`` returns raw ``data`` instead of ``handler(...)``; fix via subclass."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Self, cast, override

from pydanja import DANJAResource
from pydantic import model_validator
from pydantic.functional_validators import ModelWrapValidatorHandler


class MetaxDANJAResource[ResourceT](DANJAResource[ResourceT]):
    @model_validator(mode="wrap")
    @classmethod
    @override
    def ignore_included(cls, data: Any, handler: ModelWrapValidatorHandler[Self]) -> Self:
        data_copy = deepcopy(data)
        if hasattr(data_copy, "included"):
            del data_copy.included

        return handler(data_copy)

    @classmethod
    @override
    def from_basemodel(
        cls, resource: ResourceT, resource_name: str | None = None, resource_id: str | None = None
    ) -> Self:
        return cast(
            Self, super().from_basemodel(resource=resource, resource_name=resource_name, resource_id=resource_id)
        )
