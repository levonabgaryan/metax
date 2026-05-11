import logging
from typing import TYPE_CHECKING, Any, cast, override

from asgiref.sync import async_to_sync
from django.contrib import admin
from django.db.models import QuerySet
from django.forms import ModelForm
from django.http import HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from django_framework.metax.models import CategoryHelperWordsModel
from metax.core.application.cud_services.category import (
    AddNewHelperWordsRequestDTO,
    AddNewHelperWordsService,
    DeleteHelperWordRequestDTO,
    DeleteHelperWordService,
    HelperWordPayloadRequestDTO,
    UpdateHelperWordTextRequestDTO,
    UpdateHelperWordTextService,
)
from metax_bootstrap import METAX_LIFESPAN_MANAGER

if TYPE_CHECKING:
    _ModelAdminBase = admin.ModelAdmin[CategoryHelperWordsModel]
else:
    _ModelAdminBase = admin.ModelAdmin

csrf_protect_m = method_decorator(csrf_protect)

logger = logging.getLogger(__name__)


@admin.register(CategoryHelperWordsModel)
class CategoryHelperWordsAdmin(_ModelAdminBase):
    list_display = ("uuid", "helper_word_text", "category", "created_at", "updated_at")
    list_display_links = ("helper_word_text",)

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
        obj: CategoryHelperWordsModel,
        form: ModelForm[CategoryHelperWordsModel],
        change: bool,
    ) -> None:
        metax_container = METAX_LIFESPAN_MANAGER.get_metax_container()
        unit_of_work_provider = metax_container.get_unit_of_work_provider()
        event_bus = async_to_sync(metax_container.get_event_bus)()

        if change:
            request_dto_ = UpdateHelperWordTextRequestDTO(
                category_uuid=obj.category.uuid,
                helper_word_uuid=obj.uuid,
                new_text=form.cleaned_data["helper_word_text"],
            )
            cud_service_ = UpdateHelperWordTextService(
                unit_of_work_provider=unit_of_work_provider, event_bus=event_bus
            )
            async_to_sync(cud_service_.execute)(request_dto_)
        else:
            request_dto = AddNewHelperWordsRequestDTO(
                category_uuid=form.cleaned_data["category"].uuid,
                new_helper_word_payload=HelperWordPayloadRequestDTO(
                    helper_word_text=form.cleaned_data["helper_word_text"],
                ),
            )
            cud_service = AddNewHelperWordsService(
                unit_of_work_provider=unit_of_work_provider,
                event_bus=event_bus,
            )
            response_dto = async_to_sync(cud_service.execute)(request_dto)
            obj.uuid = response_dto.new_helper_word_payload.helper_word_uuid
        obj.refresh_from_db()
        self.message_user(request, f"save_model called, change={change}")

    @override
    def delete_model(self, request: HttpRequest, obj: CategoryHelperWordsModel) -> None:
        metax_container = METAX_LIFESPAN_MANAGER.get_metax_container()
        unit_of_work_provider = metax_container.get_unit_of_work_provider()
        event_bus = async_to_sync(metax_container.get_event_bus)()

        request_dto = DeleteHelperWordRequestDTO(
            helper_word_uuid=obj.uuid,
            category_uuid=obj.category.uuid,
        )
        cud_service = DeleteHelperWordService(
            unit_of_work_provider=unit_of_work_provider,
            event_bus=event_bus,
        )
        async_to_sync(cud_service.execute)(request_dto)

    @override
    def delete_queryset(self, request: HttpRequest, queryset: QuerySet[CategoryHelperWordsModel]) -> None:
        for helper_word in queryset:
            self.delete_model(request, helper_word)
