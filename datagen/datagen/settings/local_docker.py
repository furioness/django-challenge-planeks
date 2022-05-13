import dj_database_url

from .base import *


DATABASES["default"] = dj_database_url.config(default="postgres://datagen:datagen@localhost:54321/datagen")


CELERY_BROKER = "pyamqp://@localhost//"
