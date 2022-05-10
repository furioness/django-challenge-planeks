from os import environ

import dj_database_url

from .base import *


DEBUG = False

SECRET_KEY = environ["SECRET_KEY"]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

ALLOWED_HOSTS = ["datagen-challenge.herokuapp.com"]

DATABASES["default"] = dj_database_url.config(default=environ["DATABASE_URL"])

INSTALLED_APPS += ["storages"]

AWS_ACCESS_KEY_ID = environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = environ["AWS_SECRET_ACCESS_KEY"]
AWS_STORAGE_BUCKET_NAME = environ["AWS_STORAGE_BUCKET_NAME"]

AWS_DEFAULT_ACL = "public-read"
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
# s3 static settings
AWS_STATIC_LOCATION = "static"
STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_STATIC_LOCATION}/"
STATICFILES_STORAGE = "datagen.storage_backends.StaticStorage"
# why MEDIA_URL works for custom storage?

# https://www.cloudamqp.com/docs/celery.html
CELERY_BROKER = environ["CLOUDAMQP_URL"]
CELERY_BROKER_POOL_LIMIT = 1  # Will decrease connection usage
CELERY_BROKER_HEARTBEAT = None  # We're using TCP keep-alive instead
CELERY_BROKER_CONNECTION_TIMEOUT = (
    30  # May require a long timeout due to Linux DNS timeouts etc
)
CELERY_RESULT_BACKEND = (
    None  # AMQP is not recommended as result backend as it creates thousands of queues
)
CELERY_EVENT_QUEUE_EXPIRES = (
    300  # Will delete all celeryev. queues without consumers after x seconds.
)
CELERY_WORKER_PREFETCH_MULTIPLIER = (
    1  # Disable prefetching, it's causes problems and doesn't help performance
)
CELERY_WORKER_CONCURRENCY = 1  # If you tasks are CPU bound, then limit to the number of cores, otherwise increase substainally
