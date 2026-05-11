from collections.abc import Coroutine
from types import CoroutineType
from typing import TYPE_CHECKING, Any, override

from taskiq import TaskiqMessage, TaskiqMiddleware, TaskiqResult

if TYPE_CHECKING:
    from django_framework.metax.models.taskiq import TaskiqModel


def _get_taskiq_model() -> type[TaskiqModel]:
    from django_framework.metax.models.taskiq import TaskiqModel

    return TaskiqModel


class DjangoAdminTaskiqMiddleware(TaskiqMiddleware):
    @override
    def pre_send(
        self,
        message: TaskiqMessage,
    ) -> TaskiqMessage | Coroutine[Any, Any, TaskiqMessage] | CoroutineType[Any, Any, TaskiqMessage]:
        async def _impl() -> TaskiqMessage:
            taskiq_model = _get_taskiq_model()
            raw_request_id = message.labels.get("request_id") or message.kwargs.get("request_id")
            request_id = str(raw_request_id) if raw_request_id is not None else ""
            await taskiq_model._default_manager.acreate(  # noqa: SLF001
                task_id=message.task_id,
                task_name=message.task_name,
                request_id=request_id,
                status=taskiq_model.Status.PENDING,
            )
            return message

        return _impl()

    @override
    def on_error(
        self,
        message: TaskiqMessage,
        result: TaskiqResult[Any],
        exception: BaseException,
    ) -> Coroutine[Any, Any, None] | CoroutineType[Any, Any, None] | None:
        async def _impl() -> None:
            taskiq_model = _get_taskiq_model()
            await taskiq_model._default_manager.filter(task_id=message.task_id).aupdate(  # noqa: SLF001
                status=taskiq_model.Status.FAILED,
                error_message=str(exception),
            )

        return _impl()

    @override
    def post_execute(
        self,
        message: TaskiqMessage,
        result: TaskiqResult[Any],
    ) -> Coroutine[Any, Any, None] | CoroutineType[Any, Any, None] | None:
        async def _impl() -> None:
            taskiq_model = _get_taskiq_model()
            status = taskiq_model.Status.SUCCESS if not result.is_err else taskiq_model.Status.FAILED
            error = str(result.error) if result.is_err else ""
            await taskiq_model._default_manager.filter(task_id=message.task_id).aupdate(  # noqa: SLF001
                status=status, error_message=error
            )

        return _impl()
