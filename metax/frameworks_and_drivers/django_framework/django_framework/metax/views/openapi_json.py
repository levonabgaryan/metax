"""Serve OpenAPI JSON like :class:`dmr.openapi.views.json.OpenAPIJsonView`, then post-process with pydanja."""

from typing import override

from django.http import HttpRequest, HttpResponse
from dmr.openapi.dump import json_dump
from dmr.openapi.views.json import OpenAPIJsonView
from pydanja.openapi import danja_openapi


class DanjaOpenAPIJsonView(OpenAPIJsonView):
    @override
    def get(self, request: HttpRequest) -> HttpResponse:
        schema_dict = self.schema.convert(skip_validation=self.skip_validation)
        polished = danja_openapi(schema_dict)
        return HttpResponse(
            content=json_dump(polished),
            content_type=self.content_type,
        )
