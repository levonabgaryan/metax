"""GET collection for discounted products (search + pagination wiring lives here; extend as needed)."""

import datetime as dt
from http import HTTPStatus
from uuid import UUID

from dmr import Query, modify
from pydanja import DANJARelationship, DANJAResourceIdentifier, DANJASingleResource

from django_framework.metax.views.category.resources import CategoryResource, CategoryResponseBody
from django_framework.metax.views.discounted_product.resources import (
    DiscountedProductListResponseBody,
    DiscountedProductResource,
    QueryParamsForCollection,
    discounted_product_read_model_to_resource,
)
from django_framework.metax.views.json_api_controller import MetaxJsonApiController
from django_framework.metax.views.retailer.resources import RetailerResource, RetailerResponseBody
from metax.core.application.read_models.discounted_product import (
    DiscountedProductCategoryReadModel,
    DiscountedProductReadModel,
    DiscountedProductRetailerReadModel,
)
from metax.frameworks_and_drivers.pydanja_.pydanja_resource import RESOURCE_TYPE_CATEGORY, RESOURCE_TYPE_RETAILER
from metax_bootstrap import METAX_LIFESPAN_MANAGER

type _IncludedSingleResourceUnion = DANJASingleResource[CategoryResource] | DANJASingleResource[RetailerResource]


class DiscountedProductCollectionController(MetaxJsonApiController):
    @modify(status_code=HTTPStatus.OK, tags=["Discounted product"], auth=None)
    async def get(self, parsed_query: Query[QueryParamsForCollection]) -> DiscountedProductListResponseBody:
        container = METAX_LIFESPAN_MANAGER.get_metax_container()
        read_repo = await container.get_discounted_product_read_model_repository()
        if parsed_query.category_uuid is not None:
            (
                discounted_product_read_models,
                total_matching_documents_count,
            ) = await read_repo.search_by_name_and_by_category_uuid(
                name=parsed_query.matched_discounted_product_name,
                category_uuid=str(parsed_query.category_uuid),
                offset=parsed_query.offset,
                limit=parsed_query.limit,
            )
        else:
            discounted_product_read_models, total_matching_documents_count = await read_repo.search_by_name(
                name=parsed_query.matched_discounted_product_name,
                offset=parsed_query.offset,
                limit=parsed_query.limit,
            )
        response_body = DiscountedProductListResponseBody.from_basemodel_list(
            resources=[
                discounted_product_read_model_to_resource(read_model)
                for read_model in discounted_product_read_models
            ],
        )

        if parsed_query.include is not None:
            self.__fill_relationships(
                discounted_product_read_models=discounted_product_read_models,
                response_body=response_body,
            )
            self.__fill_included_field(
                discounted_product_read_models=discounted_product_read_models, response_body=response_body
            )

        response_body.links = self._build_pagination_links(
            self.request.build_absolute_uri(),
            offset=parsed_query.offset,
            limit=parsed_query.limit,
            total_count=total_matching_documents_count,
        )
        return response_body

    @staticmethod
    def __fill_included_field(
        discounted_product_read_models: list[DiscountedProductReadModel],
        response_body: DiscountedProductListResponseBody,
    ) -> None:
        """Append compound retailer/category documents to ``included``, deduplicated by JSON:API type + id.

        Retailer is required on every read model; category is optional. Do not use ``elif`` between them.
        """
        deduplicated_included_resources_by_json_api_type_and_id: dict[
            tuple[str, str], _IncludedSingleResourceUnion
        ] = {}

        for read_model in discounted_product_read_models:
            retailer_fragment: DiscountedProductRetailerReadModel = read_model["retailer"]
            retailer_compound_key = (RESOURCE_TYPE_RETAILER, str(retailer_fragment["uuid_"]))
            if retailer_compound_key not in deduplicated_included_resources_by_json_api_type_and_id:
                deduplicated_included_resources_by_json_api_type_and_id[retailer_compound_key] = (
                    RetailerResponseBody.from_basemodel(
                        resource=RetailerResource(
                            retailer_uuid=UUID(retailer_fragment["uuid_"]),
                            created_at=dt.datetime.fromisoformat(retailer_fragment["created_at"]),
                            updated_at=dt.datetime.fromisoformat(retailer_fragment["updated_at"]),
                            name=retailer_fragment["name"],
                            home_page_url=retailer_fragment["home_page_url"],
                            phone_number=retailer_fragment["phone_number"],
                        )
                    ).data
                )

            if "category" in read_model:
                category_fragment: DiscountedProductCategoryReadModel = read_model["category"]
                category_compound_key = (RESOURCE_TYPE_CATEGORY, str(category_fragment["uuid_"]))
                if category_compound_key not in deduplicated_included_resources_by_json_api_type_and_id:
                    deduplicated_included_resources_by_json_api_type_and_id[category_compound_key] = (
                        CategoryResponseBody.from_basemodel(
                            resource=CategoryResource(
                                category_uuid=UUID(category_fragment["uuid_"]),
                                created_at=dt.datetime.fromisoformat(category_fragment["created_at"]),
                                updated_at=dt.datetime.fromisoformat(category_fragment["updated_at"]),
                                name=category_fragment["name"],
                            )
                        ).data
                    )

        response_body.included = list(deduplicated_included_resources_by_json_api_type_and_id.values())

    @staticmethod
    def __fill_relationships(
        *,
        discounted_product_read_models: list[DiscountedProductReadModel],
        response_body: DiscountedProductListResponseBody,
    ) -> None:
        """Set ``data[].relationships`` so each primary resource links to its retailer and optional category."""
        discounted_product_resources: list[DANJASingleResource[DiscountedProductResource]] = response_body.data
        for dp_resource, read_model in zip(
            discounted_product_resources,
            discounted_product_read_models,
            strict=True,
        ):
            retailer_fragment = read_model["retailer"]
            relationships: dict[str, DANJARelationship] = {
                RESOURCE_TYPE_RETAILER: DANJARelationship(
                    data=DANJAResourceIdentifier(
                        id=str(retailer_fragment["uuid_"]),
                        type=RESOURCE_TYPE_RETAILER,
                    ),
                ),
            }
            if "category" in read_model:
                category_fragment = read_model["category"]
                relationships[RESOURCE_TYPE_CATEGORY] = DANJARelationship(
                    data=DANJAResourceIdentifier(
                        id=str(category_fragment["uuid_"]),
                        type=RESOURCE_TYPE_CATEGORY,
                    ),
                )
            dp_resource.relationships = relationships
