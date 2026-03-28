from django.urls import URLResolver, URLPattern, path, include
from dmr.openapi import build_schema
from dmr.openapi.views import OpenAPIJsonView, RedocView, ScalarView, SwaggerView

from .controllers import router as health_check_router

health_check_schema = build_schema(health_check_router)
health_check_url_patterns: list[URLResolver | URLPattern] = [
    path(health_check_router.prefix, include(health_check_router.urls)),
    path("docs/openapi.json/", OpenAPIJsonView.as_view(health_check_schema), name="openapi"),
    path("docs/redoc/", RedocView.as_view(health_check_schema), name="redoc"),
    path("docs/scalar/", ScalarView.as_view(health_check_schema), name="scalar"),
    path("docs/swagger/", SwaggerView.as_view(health_check_schema), name="swagger"),
]
