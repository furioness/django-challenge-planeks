from os import environ

import dj_database_url

from .base import *


DEBUG = False

SECRET_KEY = environ['SECRET_KEY']
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

ALLOWED_HOSTS = ['datagen-challenge.herokuapp.com']

DATABASES['default'] = dj_database_url.config(default=environ['DATABASE_URL'])

# https://www.cloudamqp.com/docs/celery.html
CELERY_BROKER = environ['CLOUDAMQP_URL']
CELERY_BROKER_POOL_LIMIT = 1 # Will decrease connection usage
CELERY_BROKER_HEARTBEAT = None # We're using TCP keep-alive instead
CELERY_BROKER_CONNECTION_TIMEOUT = 30 # May require a long timeout due to Linux DNS timeouts etc
CELERY_RESULT_BACKEND = None # AMQP is not recommended as result backend as it creates thousands of queues
CELERY_EVENT_QUEUE_EXPIRES = 300 # Will delete all celeryev. queues without consumers after x seconds.
CELERY_WORKER_PREFETCH_MULTIPLIER = 1 # Disable prefetching, it's causes problems and doesn't help performance
CELERY_WORKER_CONCURRENCY = 2 # If you tasks are CPU bound, then limit to the number of cores, otherwise increase substainally