import atexit
import logging
import queue
import sys
from logging.handlers import QueueListener, QueueHandler

from config_ import discount_service_configs

if discount_service_configs.debug:
    log_level = logging.DEBUG
else:
    log_level = logging.INFO

LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)s %(threadName)s] [%(name)s] [%(message)s]"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

root_logger = logging.getLogger()
root_logger.setLevel(log_level)

formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
console_handler.setLevel(log_level)

file_handler = logging.FileHandler("discount_service.log", mode="a", encoding="utf-8")
file_handler.setFormatter(formatter)
file_handler.setLevel(log_level)

# --- Side-libraries logging levels configuration ---
PACKAGE_LOG_LEVEL = logging.DEBUG if discount_service_configs.debug else logging.WARNING
packages_loggers_names = [
    "django",
    "django.db.backends",
    "django.utils.autoreload",
    "urllib3",
    "httpx",
    "opensearch",
    "celery",
    "amqp",
    "kombu",
    "asyncio",
    "httpcore",
]
for logger_name in packages_loggers_names:
    logger = logging.getLogger(logger_name)
    logger.setLevel(PACKAGE_LOG_LEVEL)

# --- Async-friendly logging (Non-blocking) ---
log_queue: queue.Queue[logging.LogRecord] = queue.Queue(-1)
queue_handler = QueueHandler(queue=log_queue)
handlers: list[logging.Handler] = [console_handler, file_handler]
listener = QueueListener(log_queue, *handlers, respect_handler_level=True)
root_logger.addHandler(queue_handler)

# --- Lifecycle management ---
# Start the background listener thread and ensure it drains the queue on exit
listener.start()

atexit.register(listener.stop)
