import contextvars
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import override

request_id_ctx = contextvars.ContextVar("request_id", default="-")


def get_request_id() -> str:
    return request_id_ctx.get()


@contextmanager
def request_id_scope(request_id: str) -> Iterator[None]:
    """Bind request id for the current context (HTTP request, Celery task, etc.)."""
    token = request_id_ctx.set(request_id)
    try:
        yield
    finally:
        request_id_ctx.reset(token)


class RequestIdFilter(logging.Filter):
    @override
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True
