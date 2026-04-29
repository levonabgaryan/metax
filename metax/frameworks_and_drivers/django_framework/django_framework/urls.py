"""URL configuration for django_framework project.

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
from django_framework.metax.admin.site import admin_site
from django_framework.metax.views.category.collection_controller import CategoryCollectionController
from django_framework.metax.views.category.resource_controller import CategoryResourceController
from django_framework.metax.views.category_helper_word.collection_controller import (
    CategoryHelperWordCollectionController,
)
from django_framework.metax.views.celery.tasks import CollectDiscountedProductsFromRetailersController
from django_framework.metax.views.health.controllers import HealthCheckView
from django_framework.metax.views.openapi_json import DanjaOpenAPIJsonView
from django_framework.metax.views.retailer.collection_controller import (
    RetailerCollectionController,
)
from django_framework.metax.views.retailer.resource_controller import RetailerResourceController
from dmr.openapi import build_schema
from dmr.openapi.views import RedocView, SwaggerView
from dmr.routing import Router, path

from metax.frameworks_and_drivers.pydanja_.pydanja_resource import (
    RESOURCE_TYPE_CATEGORY,
    RESOURCE_TYPE_CATEGORY_HELPER_WORD,
    RESOURCE_TYPE_RETAILER,
)

api_router = Router(
    prefix="api/",
    urls=[
        path("health-check/", HealthCheckView.as_view()),
        path(f"{RESOURCE_TYPE_CATEGORY}/", CategoryCollectionController.as_view()),
        path(f"{RESOURCE_TYPE_CATEGORY}/<uuid:category_uuid>/", CategoryResourceController.as_view()),
        path(f"{RESOURCE_TYPE_CATEGORY_HELPER_WORD}/", CategoryHelperWordCollectionController.as_view()),
        path(f"{RESOURCE_TYPE_RETAILER}/", RetailerCollectionController.as_view()),
        path(f"{RESOURCE_TYPE_RETAILER}/<uuid:retailer_uuid>/", RetailerResourceController.as_view()),
        path("celery-collect-discounted-products/", CollectDiscountedProductsFromRetailersController.as_view()),
    ],
)
api_schema = build_schema(api_router)

urlpatterns = [
    path("admin/", admin_site.urls),
    path(api_router.prefix, include((api_router.urls, "api"))),
    path(
        "docs/openapi.json/",
        DanjaOpenAPIJsonView.as_view(api_schema),
        name="api_openapi",
    ),
    path("docs/swagger/", SwaggerView.as_view(api_schema)),
    path("docs/redoc/", RedocView.as_view(api_schema)),
    path("docs/openapi.json/", DanjaOpenAPIJsonView.as_view(api_schema), name="openapi"),
]
