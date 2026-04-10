from django.db import models
from django.db.models.functions import Now
from django_stubs_ext.db.models import TypedModelMeta


class BaseDbModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())
    updated_at = models.DateTimeField(auto_now=True, db_default=Now())

    class Meta(TypedModelMeta):
        abstract = True
