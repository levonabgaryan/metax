"""Django admin for :class:`~django_framework.metax.models.retailer.RetailerModel`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from asgiref.sync import async_to_sync
from django.contrib import admin
from django.db.models import QuerySet
from django.forms import ModelForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.views.decorators.csrf import csrf_protect

from django_framework.metax.models.retailer import RetailerModel
from metax.core.application.cud_services.retailer import (
    CreateRetailerRequestDTO,
    CreateRetailerService,
    DeleteRetailerRequestDTO,
    DeleteRetailerService,
    UpdateRetailerRequestDTO,
    UpdateRetailerService,
)
from metax.frameworks_and_drivers.taskiq_framework.tasks import (
    taskiq_collect_discounted_products_for_retailer,
)
from metax_bootstrap import METAX_LIFESPAN_MANAGER
from metax_logger.request_id_filter import get_request_id

if TYPE_CHECKING:
    _ModelAdminBase = admin.ModelAdmin[RetailerModel]
else:
    _ModelAdminBase = admin.ModelAdmin

csrf_protect_m = method_decorator(csrf_protect)


@admin.register(RetailerModel)
class RetailerAdmin(_ModelAdminBase):
    list_display = (
        "uuid",
        "name",
        "default_category",
        "home_page_url",
        "phone_number",
        "created_at",
        "updated_at",
        "run_crawler_button",
    )
    list_display_links = ("name",)
    list_select_related = ("default_category",)
    search_fields = ("name", "home_page_url", "phone_number")
    # Two ways to trigger a manual single-retailer crawl: a per-row button (below, most discoverable)
    # and a bulk "Actions" dropdown entry for kicking off several at once.
    actions = ("run_crawler",)

    def _enqueue_crawl(self, retailer_name: str) -> str:
        """Enqueue one ``CollectDiscountedProductsForRetailer`` job.

        Returns:
            The request id the run is enqueued under (for correlating its logs / TaskiqModel row).
        """
        request_id = get_request_id()
        async_to_sync(taskiq_collect_discounted_products_for_retailer.kiq)(
            retailer_name=retailer_name, request_id=request_id
        )
        return request_id

    @admin.display(description="Crawl")
    def run_crawler_button(self, obj: RetailerModel) -> str:
        """Render a per-row button that runs just this retailer's crawler.

        Returns:
            The HTML for a button linking to this retailer's ``run-crawler`` admin view.
        """
        url = reverse("admin:metax_retailermodel_run_crawler", args=[obj.uuid])
        return format_html('<a class="button" href="{}">▶ Run crawler</a>', url)

    def run_crawler_view(self, request: HttpRequest, retailer_uuid: str) -> HttpResponse:
        """Enqueue a manual crawl for a single retailer, then return to the changelist.

        Returns:
            A redirect back to the retailer changelist.
        """
        retailer = self.get_object(request, retailer_uuid)
        if retailer is None:
            self.message_user(request, "Retailer not found.", level="error")
        else:
            request_id = self._enqueue_crawl(retailer.name)
            self.message_user(
                request, f"Crawl enqueued for {retailer.name} (request_id={request_id})."
            )
        return redirect("admin:metax_retailermodel_changelist")

    @override
    def get_urls(self) -> list[Any]:
        custom_urls = [
            path(
                "<uuid:retailer_uuid>/run-crawler/",
                self.admin_site.admin_view(self.run_crawler_view),
                name="metax_retailermodel_run_crawler",
            ),
        ]
        return custom_urls + super().get_urls()

    @admin.action(description="Run crawler for selected retailer(s)")
    def run_crawler(self, request: HttpRequest, queryset: QuerySet[RetailerModel]) -> None:
        """Enqueue a manual single-retailer crawl per selected retailer.

        Each row becomes its own ``CollectDiscountedProductsForRetailer`` job — independently
        tracked and independently re-runnable — while the nightly all-retailers job is untouched.
        The step-2 publish swap is scoped to each retailer, so re-running one leaves the others' live
        rows in place.
        """
        enqueued = [retailer.name for retailer in queryset]
        for name in enqueued:
            self._enqueue_crawl(name)
        self.message_user(
            request, f"Crawl enqueued for {len(enqueued)} retailer(s): {', '.join(enqueued)}."
        )

    @csrf_protect_m
    @override
    def changeform_view(
        self,
        request: HttpRequest,
        object_id: str | None = None,
        form_url: str = "",
        extra_context: dict[str, Any] | None = None,
    ) -> HttpResponse:
        # ``ModelAdmin.changeform_view`` wraps ``_changeform_view`` in ``transaction.atomic()``.
        # ``super().changeform_view`` keeps that wrapper → connection/pool issues with services.
        # Call the parent implementation of the inner view only (no extra ``atomic`` here).
        return cast(
            HttpResponse,
            self._changeform_view(request, object_id, form_url, extra_context),  # type: ignore[attr-defined]
        )

    @csrf_protect_m
    @override
    def delete_view(
        self, request: HttpRequest, object_id: str, extra_context: dict[str, Any] | None = None
    ) -> HttpResponse:
        return cast(
            HttpResponse,
            self._delete_view(request, object_id, extra_context),  # type: ignore[attr-defined]
        )

    @csrf_protect_m
    @override
    def save_model(
        self,
        request: HttpRequest,
        obj: RetailerModel,
        form: ModelForm[RetailerModel],
        change: bool,
    ) -> None:
        metax_container = METAX_LIFESPAN_MANAGER.get_metax_container()
        unit_of_work_provider = metax_container.get_unit_of_work_provider()
        event_bus = async_to_sync(metax_container.get_event_bus)()
        # ``default_category`` is a CategoryModel instance (or None when cleared); the services take
        # its UUID.
        default_category = form.cleaned_data.get("default_category")
        default_category_uuid = default_category.uuid if default_category is not None else None
        if change:
            cud_service_ = UpdateRetailerService(
                event_bus=event_bus,
                unit_of_work_provider=unit_of_work_provider,
            )
            request_dto_ = UpdateRetailerRequestDTO(
                retailer_uuid=obj.uuid,
                new_name=form.cleaned_data.get("name"),
                new_phone_number=form.cleaned_data.get("phone_number"),
                new_home_page_url=form.cleaned_data.get("home_page_url"),
                new_default_category_uuid=default_category_uuid,
                set_default_category=True,
            )
            response_dto_ = async_to_sync(cud_service_.execute)(request_dto_)
            obj.uuid = response_dto_.retailer_uuid

        else:
            cud_service = CreateRetailerService(
                event_bus=event_bus,
                unit_of_work_provider=unit_of_work_provider,
            )
            request_dto = CreateRetailerRequestDTO(
                name=form.cleaned_data["name"],
                phone_number=form.cleaned_data["phone_number"],
                home_page_url=form.cleaned_data["home_page_url"],
                default_category_uuid=default_category_uuid,
            )

            response_dto = async_to_sync(cud_service.execute)(request_dto)

            obj.uuid = response_dto.retailer_uuid

        obj.refresh_from_db()

    @override
    def delete_model(self, request: HttpRequest, obj: RetailerModel) -> None:
        metax_container = METAX_LIFESPAN_MANAGER.get_metax_container()
        unit_of_work_provider = metax_container.get_unit_of_work_provider()
        event_bus = async_to_sync(metax_container.get_event_bus)()
        cud_service = DeleteRetailerService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
        request_dto = DeleteRetailerRequestDTO(
            retailer_uuid=obj.uuid,
        )
        async_to_sync(cud_service.execute)(request_dto)

    @override
    def delete_queryset(self, request: HttpRequest, queryset: QuerySet[RetailerModel]) -> None:
        for obj in queryset:
            self.delete_model(request, obj)
