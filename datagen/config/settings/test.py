from .local_docker import *
from pathlib import Path

# Using the same database  for tests as Django creates separate temporal testing database

CELERY_BROKER = "pyamqp://@localhost/testing"

# For templates coverage plugin
TEMPLATES[0]["OPTIONS"]["debug"] = True  # type: ignore[index]

MEDIA_ROOT = Path("/tmp/testmedia/")
