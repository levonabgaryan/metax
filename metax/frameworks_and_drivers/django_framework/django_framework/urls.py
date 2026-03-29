"""
URL configuration for django_framework project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import include
from dmr.openapi import build_schema
from dmr.openapi.views import OpenAPIJsonView, SwaggerView, RedocView
from dmr.routing import Router, path
from django_framework.metax.admin.site import admin_site
from django_framework.metax.views.category.controllers import CreateCategoryController
from django_framework.metax.views.health.controllers import HealthCheckView

api_router = Router(
    prefix="api/",
    urls=[
        path("health-check/", HealthCheckView.as_view(), name="health-check"),
        path("category/create/", CreateCategoryController.as_view(), name="category-create"),
    ],
)
api_schema = build_schema(api_router)

urlpatterns = [
    path("admin/", admin_site.urls),
    path(api_router.prefix, include((api_router.urls, "api"), namespace="api")),
    path(
        "docs/openapi.json/",
        OpenAPIJsonView.as_view(api_schema),
        name="api_openapi",
    ),
    path("docs/swagger/", SwaggerView.as_view(api_schema), name="api_swagger"),
    path("docs/redoc/", RedocView.as_view(api_schema), name="api_redoc"),
]
