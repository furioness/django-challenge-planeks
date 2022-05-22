import dj_database_url

from .local_docker import *


DATABASES["default"] = dj_database_url.config(
    default="postgres://datagen_testing:datagen_testing@localhost:54322/datagen_testing"
)


CELERY_BROKER = "pyamqp://@localhost:5673//"
