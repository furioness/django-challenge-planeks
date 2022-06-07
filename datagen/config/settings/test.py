from .local_docker import *

# Using the same database  for tests as Django creates separate temporal testing database

CELERY_BROKER = "pyamqp://@localhost/testing"

TEMPLATES[0]["OPTIONS"]["debug"] = True  # For templates coverage plugin
SECRET_KEY = (
    "test-secret!!!-*uai@*zrp=zf3=)1um#x)y*%gw_9pi(@z%@4*+!o)^j$x)gtu5"
)
