from datetime import datetime
from decimal import Decimal
from typing import Annotated, Self, override
from uuid import UUID

from django_framework.metax.views.category.resources import CategoryResource
from django_framework.metax.views.retailer.resources import RetailerResource
from pydanja import DANJASingleResource
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel
from pydantic.json_schema import SkipJsonSchema

from metax.core.application.read_models.discounted_product import DiscountedProductReadModel
from metax.frameworks_and_drivers.pydanja_.pydanja_resource import (
    RESOURCE_TYPE_DISCOUNTED_PRODUCT,
    MetaxDANJAResourceList,
)


class QueryParamsForCollection(BaseModel):
    """JSON:API query parameter family for search + offset pagination.

    Example:
        ``?filter[match]=wine&page[offset]=0&page[limit]=20&include=retailer,category``
    """

    offset: Annotated[int, Field(ge=0, alias="page[offset]")]
    limit: Annotated[int, Field(ge=1, alias="page[limit]")]
    filter: Annotated[str, Field(min_length=1, max_length=500, alias="filter[match]")]
    include: Annotated[str | None, Field(default=None, alias="include")] = None

    @model_validator(mode="after")
    def validate_include_requires_both_relationships(self) -> Self:
        if self.include is None:
            return self
        tokens = {part.strip() for part in self.include.split(",") if part.strip()}
        if not {"category", "retailer"}.issubset(tokens):
            msg = "include must list both 'category' and 'retailer' when provided."
            raise ValueError(msg)
        return self


class DiscountedProductResource(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"resource_name": RESOURCE_TYPE_DISCOUNTED_PRODUCT},
        populate_by_name=True,
        alias_generator=to_camel,
    )
    discounted_product_uuid: Annotated[
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
    real_price: Decimal
    discounted_price: Decimal
    url: str
    name: str


def discounted_product_read_model_to_resource(read_model: DiscountedProductReadModel) -> DiscountedProductResource:
    return DiscountedProductResource(
        discounted_product_uuid=UUID(read_model["uuid_"]),
        created_at=datetime.fromisoformat(read_model["created_at"]),
        updated_at=datetime.fromisoformat(read_model["updated_at"]),
        real_price=Decimal(str(read_model["real_price"])),
        discounted_price=Decimal(str(read_model["discounted_price"])),
        name=read_model["name"],
        url=read_model["url"],
    )


class DiscountedProductListResponseBody(MetaxDANJAResourceList[DiscountedProductResource]):
    """Primary ``data`` plus optional ``included`` when the client passes ``?include=…``."""

    included: list[DANJASingleResource[CategoryResource] | DANJASingleResource[RetailerResource]] | None = None

    @classmethod
    @override
    def from_basemodel_list(
        cls,
        resources: list[DiscountedProductResource],
        resource_name: str | None = None,
        resource_id: str | None = None,
    ) -> Self:
        return super().from_basemodel_list(
            resources=resources, resource_name=resource_name, resource_id=resource_id
        )
