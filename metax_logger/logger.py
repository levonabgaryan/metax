import atexit
import logging
import queue
import sys
from logging.handlers import QueueHandler, QueueListener

from metax_configs import BaseConfigs

LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)s %(threadName)s] [%(name)s] [%(message)s]"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_listener: QueueListener | None = None

PACKAGES_TO_MUTE = [
    "django",
    "django.db.backends",
    "django.utils.autoreload",
    "urllib3",
    "httpx",
    "opensearch",
    "opensearchpy",
    "celery",
    "amqp",
    "kombu",
    "asyncio",
    "httpcore",
]


def init_logger(metax_configs: BaseConfigs) -> None:
    """Initializes a global non-blocking logging system using a QueueListener.

    This setup ensures that logging operations do not block the main application thread,
    which is critical for high-performance and asynchronous applications.

    Note: Do not forgit call this method in application run methods.
    """
    root_logger = logging.getLogger()

    global _listener

    # In prefork environments (e.g. Celery), handlers are inherited by child
    # processes but listener threads are not. Always reinitialize safely.
    if _listener is not None:
        _listener.stop()
        _listener = None

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    log_level = logging.DEBUG if metax_configs.debug else logging.INFO
    root_logger.setLevel(log_level)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    handlers: list[logging.Handler] = [console_handler]

    log_queue: queue.Queue[logging.LogRecord] = queue.Queue(-1)

    queue_handler = QueueHandler(queue=log_queue)

    listener = QueueListener(log_queue, *handlers, respect_handler_level=True)

    root_logger.addHandler(queue_handler)

    for logger_name in PACKAGES_TO_MUTE:
        lib_logger = logging.getLogger(logger_name)
        lib_logger.setLevel(logging.WARNING)
        lib_logger.propagate = True

    # Celery logs should stay visible at INFO level.
    celery_logger = logging.getLogger("celery")
    celery_logger.setLevel(logging.INFO)
    celery_logger.propagate = True

    listener.start()
    _listener = listener
    atexit.register(listener.stop)
