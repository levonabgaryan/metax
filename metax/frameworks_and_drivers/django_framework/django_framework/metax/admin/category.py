from __future__ import annotations

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
    list_display = ("uuid", "name", "name_hy", "name_ru", "created_at", "updated_at")
    list_display_links = ("name",)
    search_fields = ("name", "name_hy", "name_ru")

    @csrf_protect_m
    @override
    def changeform_view(
        self,
        request: HttpRequest,
        object_id: str | None = None,
        form_url: str = "",
        extra_context: dict[str, Any] | None = None,
    ) -> HttpResponse:
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
            async_to_sync(
                UpdateCategoryService(
                    unit_of_work_provider=unit_of_work_provider,
                    event_bus=event_bus,
                ).execute
            )(UpdateCategoryRequestDTO(
                category_uuid=obj.uuid,
                new_name=form.cleaned_data["name"],
                new_name_hy=form.cleaned_data.get("name_hy", ""),
                new_name_ru=form.cleaned_data.get("name_ru", ""),
            ))
        else:
            response_dto = async_to_sync(
                CreateCategoryService(
                    unit_of_work_provider=unit_of_work_provider,
                    event_bus=event_bus,
                ).execute
            )(CreateCategoryRequestDTO(
                name=form.cleaned_data["name"],
                name_hy=form.cleaned_data.get("name_hy", ""),
                name_ru=form.cleaned_data.get("name_ru", ""),
            ))
            obj.uuid = response_dto.category_uuid

        # ``examples`` is auxiliary tuning data for the embedding classifier, not part of the
        # category domain entity, so persist the edited value directly (the DDD create/update
        # services above own the core name fields). Edit examples freely here to teach the
        # classifier new product words for this category.
        CategoryModel.objects.filter(uuid=obj.uuid).update(examples=obj.examples)
        obj.refresh_from_db()

    @override
    def delete_model(self, request: HttpRequest, obj: CategoryModel) -> None:
        metax_container = METAX_LIFESPAN_MANAGER.get_metax_container()
        unit_of_work_provider = metax_container.get_unit_of_work_provider()
        event_bus = async_to_sync(metax_container.get_event_bus)()
        async_to_sync(
            DeleteCategoryService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus).execute
        )(DeleteCategoryRequestDTO(category_uuid=obj.uuid))

    @override
    def delete_queryset(self, request: HttpRequest, queryset: QuerySet[CategoryModel]) -> None:
        for category in queryset:
            self.delete_model(request, category)
