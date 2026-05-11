from typing import TYPE_CHECKING

from django.contrib import admin

from django_framework.metax.models.taskiq import TaskiqModel

if TYPE_CHECKING:
    _ModelAdminBase = admin.ModelAdmin[TaskiqModel]
else:
    _ModelAdminBase = admin.ModelAdmin


@admin.register(TaskiqModel)
class TaskiqAdmin(_ModelAdminBase):
    list_display = ("task_id", "task_name", "request_id", "status", "created_at", "updated_at")
    list_display_links = ("task_id", "task_name")
    search_fields = ("task_id", "task_name", "request_id", "status")
    list_filter = ("status", "created_at")
    ordering = ("-created_at",)
