release: python manage.py migrate
web: gunicorn --pythonpath datagen config.wsgi
worker: celery --workdir datagen -A config worker -l INFO