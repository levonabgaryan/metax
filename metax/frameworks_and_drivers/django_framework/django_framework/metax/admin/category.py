from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from asgiref.sync import async_to_sync
from django import forms
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
from metax.core.application.ddd_patterns.services.category_keyword_matcher import find_keyword_conflicts
from metax_bootstrap import METAX_LIFESPAN_MANAGER

if TYPE_CHECKING:
    _ModelAdminBase = admin.ModelAdmin[CategoryModel]
    _ModelFormBase = forms.ModelForm[CategoryModel]
else:
    _ModelAdminBase = admin.ModelAdmin
    _ModelFormBase = forms.ModelForm

csrf_protect_m = method_decorator(csrf_protect)


class CategoryAdminForm(_ModelFormBase):
    class Meta:
        model = CategoryModel
        fields = "__all__"

    def clean_keywords(self) -> str:
        """Reject keywords another category already owns — an ambiguous keyword decides nothing.

        Returns:
            The submitted keywords text, unchanged.

        Raises:
            forms.ValidationError: If any keyword is also listed under another category.
        """
        keywords: str = self.cleaned_data.get("keywords", "")
        others = CategoryModel.objects.exclude(uuid=self.instance.uuid).values_list("name", "keywords")
        keywords_by_category = {name: _split_phrases(text) for name, text in others}
        keywords_by_category[self.cleaned_data.get("name") or "this category"] = _split_phrases(keywords)
        conflicts = find_keyword_conflicts(keywords_by_category)
        if conflicts:
            details = "; ".join(
                f"«{' '.join(phrase)}» is also in {', '.join(sorted(owners - {self.cleaned_data.get('name')}))}"
                for phrase, owners in sorted(conflicts.items())
            )
            msg = f"Each keyword may belong to one category only: {details}"
            raise forms.ValidationError(msg)
        return keywords


def _split_phrases(text: str) -> list[str]:
    return [part.strip() for part in text.replace(",", "\n").split("\n") if part.strip()]


@admin.register(CategoryModel)
class CategoryAdmin(_ModelAdminBase):
    form = CategoryAdminForm
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
            )(
                UpdateCategoryRequestDTO(
                    category_uuid=obj.uuid,
                    new_name=form.cleaned_data["name"],
                    new_name_hy=form.cleaned_data.get("name_hy", ""),
                    new_name_ru=form.cleaned_data.get("name_ru", ""),
                )
            )
        else:
            response_dto = async_to_sync(
                CreateCategoryService(
                    unit_of_work_provider=unit_of_work_provider,
                    event_bus=event_bus,
                ).execute
            )(
                CreateCategoryRequestDTO(
                    name=form.cleaned_data["name"],
                    name_hy=form.cleaned_data.get("name_hy", ""),
                    name_ru=form.cleaned_data.get("name_ru", ""),
                )
            )
            obj.uuid = response_dto.category_uuid

        # ``examples`` and ``keywords`` are classifier tuning data curated only here, so persist them
        # directly (the DDD create/update services above own the core name fields). Changes apply to
        # the next crawl; run scripts/reclassify_categories.py to re-apply them to current products.
        CategoryModel.objects.filter(uuid=obj.uuid).update(examples=obj.examples, keywords=obj.keywords)
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
