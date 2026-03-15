import atexit
import logging
import queue
import sys
from logging.handlers import QueueListener, QueueHandler

from config_ import discount_service_configs

LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)s %(threadName)s] [%(name)s] [%(message)s]"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

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


def init_logger() -> None:
    """
    Initializes a global non-blocking logging system using a QueueListener.

    This setup ensures that logging operations do not block the main application thread,
    which is critical for high-performance and asynchronous applications.
    """
    root_logger = logging.getLogger()

    # Prevent duplicate initialization and clear default handlers (e.g., from Pytest)
    # If handlers already exist but aren't our QueueHandler, we clear them
    # to ensure our custom formatting and non-blocking logic take precedence.
    if root_logger.hasHandlers() and not any(isinstance(h, QueueHandler) for h in root_logger.handlers):
        root_logger.handlers = []

    log_level = logging.DEBUG if discount_service_configs.debug else logging.INFO
    root_logger.setLevel(log_level)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    handlers: list[logging.Handler] = [console_handler]

    if not discount_service_configs.debug:
        file_handler = logging.FileHandler("discount_service.log", mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        handlers.append(file_handler)

    log_queue: queue.Queue[logging.LogRecord] = queue.Queue(-1)

    queue_handler = QueueHandler(queue=log_queue)

    listener = QueueListener(log_queue, *handlers, respect_handler_level=True)

    root_logger.addHandler(queue_handler)

    for logger_name in PACKAGES_TO_MUTE:
        lib_logger = logging.getLogger(logger_name)
        lib_logger.setLevel(logging.WARNING)
        lib_logger.propagate = True

    listener.start()
    atexit.register(listener.stop)
