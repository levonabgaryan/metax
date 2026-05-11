from typing import override

from django.db import models

from django_framework.metax.models.base_model import BaseDbModel


class TaskiqModel(BaseDbModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        STARTED = "STARTED", "Started"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    task_id = models.UUIDField(primary_key=True, editable=False)
    task_name = models.CharField(max_length=255)
    request_id = models.CharField(max_length=255, blank=True, default="", db_index=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True, default="")

    class Meta:
        db_table = "taskiq_tasks"
        ordering = ("-created_at",)

    @override
    def __str__(self) -> str:
        return f"{self.task_name} [{self.task_id}] - {self.status}"
