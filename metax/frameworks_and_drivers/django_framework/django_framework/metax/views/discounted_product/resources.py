import datetime as dt
from decimal import Decimal
from typing import Annotated, Self, override
from uuid import UUID

from pydanja import DANJASingleResource
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel
from pydantic.json_schema import SkipJsonSchema

from django_framework.metax.views.category.resources import CategoryResource
from django_framework.metax.views.retailer.resources import RetailerResource
from metax.core.application.read_models.discounted_product import DiscountedProductReadModel
from metax.frameworks_and_drivers.pydanja_.pydanja_resource import (
    RESOURCE_TYPE_DISCOUNTED_PRODUCT,
    MetaxDANJAResourceList,
)


class QueryParamsForCollection(BaseModel):
    offset: Annotated[int, Field(ge=0, alias="page[offset]")]
    limit: Annotated[int, Field(ge=1, alias="page[limit]")]
    # Optional so a category can be browsed without a search query (mirrors the bot's category view).
    matched_discounted_product_name: Annotated[
        str | None,
        Field(min_length=1, max_length=500, alias="filter[match][discountedProduct.name]"),
    ] = None
    category_uuid: Annotated[
        UUID | None,
        Field(alias="filter[eq][category.category_uuid]"),
    ] = None
    retailer_uuid: Annotated[
        UUID | None,
        Field(alias="filter[eq][retailer.retailer_uuid]"),
    ] = None
    include: Annotated[str | None, Field(alias="include")] = "category,retailer"

    @model_validator(mode="after")
    def validate_include_requires_both_relationships(self) -> Self:
        if self.include is None:
            return self
        tokens = {part.strip() for part in self.include.split(",") if part.strip()}
        if not {"category", "retailer"}.issubset(tokens):
            msg = "include must list both 'category' and 'retailer' when provided."
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def validate_supported_filter_combination(self) -> Self:
        """Constrain filters to the read-side queries the repository actually supports.

        Supported: name alone; name + retailer; name + category; category alone (browse). A
        request without a name must carry a category to browse, and retailer filtering only
        applies alongside a name.

        Returns:
            The validated model.

        Raises:
            ValueError: If the filter combination has no supporting read-side query.
        """
        if self.matched_discounted_product_name is None:
            if self.category_uuid is None:
                msg = "Provide a product name to search, or a category to browse."
                raise ValueError(msg)
            if self.retailer_uuid is not None:
                msg = "Retailer filtering requires a product name."
                raise ValueError(msg)
        if self.retailer_uuid is not None and self.category_uuid is not None:
            msg = "Filter by retailer or by category, not both."
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
    created_at: dt.datetime
    updated_at: dt.datetime
    real_price: Decimal
    discounted_price: Decimal
    url: str
    name: str
    # Optional: some products have no image; clients (mobile/web) fall back to a placeholder.
    image_url: str | None = None


def discounted_product_read_model_to_resource(read_model: DiscountedProductReadModel) -> DiscountedProductResource:
    return DiscountedProductResource(
        discounted_product_uuid=UUID(read_model["uuid_"]),
        created_at=dt.datetime.fromisoformat(read_model["created_at"]),
        updated_at=dt.datetime.fromisoformat(read_model["updated_at"]),
        real_price=Decimal(str(read_model["real_price"])),
        discounted_price=Decimal(str(read_model["discounted_price"])),
        name=read_model["name"],
        url=read_model["url"],
        image_url=read_model.get("image_url"),
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
