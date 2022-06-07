[![CI](https://github.com/furioness/django-challenge-planeks/actions/workflows/CI.yml/badge.svg?branch=master)](https://github.com/furioness/django-challenge-planeks/actions/workflows/CI.yml)
[![CodeQL](https://github.com/furioness/django-challenge-planeks/actions/workflows/codeql.yml/badge.svg?branch=master)](https://github.com/furioness/django-challenge-planeks/actions/workflows/codeql.yml)
[![Heroku Deployment](https://github.com/furioness/django-challenge-planeks/actions/workflows/deploy_to_heroku.yml/badge.svg?branch=master)](https://github.com/furioness/django-challenge-planeks/actions/workflows/deploy_to_heroku.yml)
![wakatime](https://wakatime.com/badge/user/43ad3009-1842-4a4f-a7fa-e8332aeecd33/project/8209bb54-1f75-4b08-8ea1-eeaa06678f8f.svg "Time in editor. Multiply by ~1.5-2.5 for the real time.")

# Junior Django dev application challenge]

## Requirements
 Check challenge requirements in *requirements* folder. Don't expect perfection (especially regarding the frontend side and git) though.

## Try online
Go to https://datagen-challenge.herokuapp.com/ (give a minute if stalled - Heroku bootup)
and use the next **credentials**:  
**username**: *preview*  
**login**: *githubtest*

## Local setup:
1. Run `docker compose up`
2. `export DJANGO_SETTINGS_MODULE=config.settings.local_docker` 

3. run `worker celery --workdir datagen -A config worker -l INFO`
or `export WORKER_LOCAL=True` to call celery task as `run()` (inprocess) instead of `delay()`

## Heroku deployment
There is no `requirements.txt`, so in order to upload to Heroku: **add [poetry build pack](https://github.com/moneymeets/python-poetry-buildpack)**   
Then add services and their credentials to environment variables (check settings.heroku module):
- Heroku CloudAMQP addon or whatever for RabbitMQ
- Heroku Postgres addon or whatever for PostgreSQL
- Amazon S3 ([walkthrough](https://testdriven.io/blog/storing-django-static-and-media-files-on-amazon-s3/)) for storing staticfiles and generated datasets (privately)

***
Check pre-commit for a simple git hook file for ensuring formatting with Black
***

## TODO:
- Add tests
- Refactor schema creation/editing to use fields as Django models and modelForms instead of hacking with JSONField (might result in even more hacking...)
- Add Django Admin model views and restricted test user
- GitHub CI/CD?
- Restrict user's row number by computational complexity that is calculated per each schema
- REST API
- User registration (forms and email related stuff)
