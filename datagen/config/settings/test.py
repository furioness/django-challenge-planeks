from .local_docker import *

# Using the same database  for tests as Django creates separate temporal testing database

CELERY_BROKER = "pyamqp://@localhost/testing"
