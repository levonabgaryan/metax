from http import HTTPStatus

from django_framework.metax.views.discounted_product.resources import (
    DiscountedProductListResponseBody,
    QueryParamsForCollection,
    discounted_product_read_model_to_resource,
)
from django_framework.metax.views.json_api_controller import MetaxJsonApiController
from dmr import Query, modify

from metax_bootstrap import get_metax_lifespan_manager


class DiscountedProductCollectionController(MetaxJsonApiController):
    @modify(
        status_code=HTTPStatus.OK,
        tags=["Discounted product"],
    )
    async def get(self, parsed_query: Query[QueryParamsForCollection]) -> DiscountedProductListResponseBody:
        container = get_metax_lifespan_manager().get_di_container()
        repos = container.repositories_container.container
        read_repo = await repos.discounted_product_read_model_repository.async_()
        read_models, total = await read_repo.search_by_name(
            name=parsed_query.filter,
            offset=parsed_query.offset,
            limit=parsed_query.limit,
        )
        resources = [discounted_product_read_model_to_resource(rm) for rm in read_models]
        response_body = DiscountedProductListResponseBody.from_basemodel_list(resources=resources)
        response_body.links = self._build_pagination_links(
            self.request.build_absolute_uri(),
            offset=parsed_query.offset,
            limit=parsed_query.limit,
            total_count=total,
        )
        return response_body
