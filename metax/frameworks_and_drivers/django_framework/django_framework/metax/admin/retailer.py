"""Django admin for :class:`~django_framework.metax.models.retailer.RetailerModel`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from asgiref.sync import async_to_sync
from django.contrib import admin
from django.db.models import QuerySet
from django.forms import ModelForm
from django.http import HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
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
from metax_bootstrap import METAX_LIFESPAN_MANAGER

if TYPE_CHECKING:
    _ModelAdminBase = admin.ModelAdmin[RetailerModel]
else:
    _ModelAdminBase = admin.ModelAdmin

csrf_protect_m = method_decorator(csrf_protect)


@admin.register(RetailerModel)
class RetailerAdmin(_ModelAdminBase):
    list_display = ("uuid", "name", "home_page_url", "phone_number", "created_at", "updated_at")
    list_display_links = ("name", "home_page_url", "phone_number")

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
