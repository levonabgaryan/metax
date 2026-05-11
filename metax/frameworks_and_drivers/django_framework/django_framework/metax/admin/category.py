from typing import TYPE_CHECKING, Any, cast, override

from asgiref.sync import async_to_sync
from django.contrib import admin
from django.db.models import QuerySet
from django.forms import ModelForm
from django.http import HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from django_framework.metax.models import CategoryModel
from metax.core.application.cud_services.category import (
    CreateCategoryRequestDTO,
    CreateCategoryService,
    DeleteCategoryRequestDTO,
    DeleteCategoryService,
    UpdateCategoryRequestDTO,
    UpdateCategoryService,
)
from metax_bootstrap import METAX_LIFESPAN_MANAGER

if TYPE_CHECKING:
    _ModelAdminBase = admin.ModelAdmin[CategoryModel]
else:
    _ModelAdminBase = admin.ModelAdmin

csrf_protect_m = method_decorator(csrf_protect)


@admin.register(CategoryModel)
class CategoryAdmin(_ModelAdminBase):
    list_display = ("uuid", "name")
    list_display_links = ("name",)

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
        obj: CategoryModel,
        form: ModelForm[CategoryModel],
        change: bool,
    ) -> None:
        metax_container = METAX_LIFESPAN_MANAGER.get_metax_container()
        unit_of_work_provider = metax_container.get_unit_of_work_provider()
        event_bus = async_to_sync(metax_container.get_event_bus)()

        if change:
            request_dto_ = UpdateCategoryRequestDTO(
                category_uuid=obj.uuid,
                new_name=form.cleaned_data["name"],
            )
            cud_service_ = UpdateCategoryService(
                unit_of_work_provider=unit_of_work_provider,
                event_bus=event_bus,
            )
            async_to_sync(cud_service_.execute)(request_dto_)
        else:
            request_dto = CreateCategoryRequestDTO(name=form.cleaned_data["name"])
            cud_service = CreateCategoryService(
                unit_of_work_provider=unit_of_work_provider,
                event_bus=event_bus,
            )
            response_dto = async_to_sync(cud_service.execute)(request_dto)
            obj.uuid = response_dto.category_uuid

        obj.refresh_from_db()

    @override
    def delete_model(self, request: HttpRequest, obj: CategoryModel) -> None:
        metax_container = METAX_LIFESPAN_MANAGER.get_metax_container()
        unit_of_work_provider = metax_container.get_unit_of_work_provider()
        event_bus = async_to_sync(metax_container.get_event_bus)()
        cud_service = DeleteCategoryService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
        request_dto = DeleteCategoryRequestDTO(category_uuid=obj.uuid)
        async_to_sync(cud_service.execute)(request_dto)

    @override
    def delete_queryset(self, request: HttpRequest, queryset: QuerySet[CategoryModel]) -> None:
        for category in queryset:
            self.delete_model(request, category)
