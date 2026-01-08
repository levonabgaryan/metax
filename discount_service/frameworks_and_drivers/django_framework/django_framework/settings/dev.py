from .base import BASE_DIR

DEBUG = True
# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db_for_dev.sqlite3",
    }
}
