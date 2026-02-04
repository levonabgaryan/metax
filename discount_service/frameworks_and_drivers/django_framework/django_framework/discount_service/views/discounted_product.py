from adrf.requests import AsyncRequest
from adrf.viewsets import ViewSet
from dependency_injector.wiring import inject, Provide
from rest_framework.decorators import action
from rest_framework.response import Response

from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.core.application.read_models.discounted_product import DiscountedProductReadModel
from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer


class DiscountedProductViewSet(ViewSet):
    @action(methods=["get"], detail=False, url_path="get-by-name")
    @inject
    async def get_by_name_page(
        self,
        request: AsyncRequest,
        unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
    ) -> Response:
        # https://stackoverflow.com/questions/38284440/drf-pagination-without-queryset#:~:text=from%20typing%20import,safe%3DFalse)
        discounted_product_name = request.query_params.get("discounted_product_name")
        scroll_id = request.query_params.get("scroll_id")
        size = int(request.query_params.get("size", 50))

        if not discounted_product_name and not scroll_id:
            return Response({"error": "discounted_product_name required"}, status=400)
        repo = unit_of_work.discounted_product_read_model_repo

        items: list[DiscountedProductReadModel]
        items, new_scroll_id = await repo.search_by_name_page(
            name=discounted_product_name,
            scroll_id=scroll_id,
            size=size,
        )

        data = {
            "results": items,
            "scroll_id": new_scroll_id,
            "has_next": bool(new_scroll_id),
        }

        return Response(data)
