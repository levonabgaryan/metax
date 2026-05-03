"""Mint a staff JWT for local Swagger — route is registered only when ``DEBUG`` is true."""

import datetime as dt
import uuid
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django_framework.metax.views.json_api_controller import (
    MetaxJsonApiController,
    json_api_single_error,
)
from dmr import APIError, modify
from dmr.security.jwt.token import JWToken
from pydantic import BaseModel


class DevAdminAccessTokenResponseBody(BaseModel):
    access_token: str


class DevAdminAccessTokenController(MetaxJsonApiController):
    @modify(status_code=HTTPStatus.OK, tags=["Development"], auth=None)
    async def get(self) -> DevAdminAccessTokenResponseBody:
        user = await get_user_model().objects.filter(is_staff=True, is_active=True).afirst()
        if user is None:
            raise APIError(
                json_api_single_error(
                    exc=RuntimeError("No active staff user; create one with createsuperuser."),
                    status=HTTPStatus.NOT_FOUND,
                ),
                status_code=HTTPStatus.NOT_FOUND,
            )
        token = JWToken(
            sub=str(user.pk),
            exp=dt.datetime.now(dt.UTC) + dt.timedelta(hours=24),
            jti=uuid.uuid4().hex,
            extras={"type": "access"},
        )
        return DevAdminAccessTokenResponseBody(
            access_token=token.encode(secret=settings.SECRET_KEY, algorithm="HS256"),
        )
