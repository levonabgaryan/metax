from typing import TYPE_CHECKING, Any, override

from asgiref.sync import async_to_sync
from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import path

from django_framework.metax.models import DiscountedProductModel
from metax.frameworks_and_drivers.taskiq_framework.tasks import (
    taskiq_collect_discounted_products_from_all_retailers,
)
from metax_logger.request_id_filter import get_request_id

if TYPE_CHECKING:
    _ModelAdminBase = admin.ModelAdmin[DiscountedProductModel]
else:
    _ModelAdminBase = admin.ModelAdmin


@admin.register(DiscountedProductModel)
class DiscountedProductAdmin(_ModelAdminBase):
    change_list_template = "admin/metax/discountedproductmodel/change_list.html"

    list_display = (
        "uuid",
        "real_price",
        "discounted_price",
        "name",
        "url",
        "retailer",
        "category",
        "created_at",
        "updated_at",
    )
    list_display_links = ("real_price", "discounted_price", "name", "url")

    @override
    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    @override
    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def run_collector_view(self, request: HttpRequest) -> HttpResponse:
        self._do_collect(request)
        return redirect("..")

    @override
    def get_urls(self) -> list[Any]:
        urls = super().get_urls()
        custom_urls = [
            path(
                "run-collector/",
                self.admin_site.admin_view(self.run_collector_view),
                name="run_collector_service",
            ),
        ]
        return custom_urls + urls

    def _do_collect(self, request: HttpRequest) -> None:
        request_id = get_request_id()
        taskiq_result = async_to_sync(taskiq_collect_discounted_products_from_all_retailers.kiq)(
            request_id=request_id
        )
        task_id = getattr(taskiq_result, "task_id", None)
        self.message_user(
            request,
            f"Collection async process has started (request_id={request_id}, task_id={task_id}).",
        )
