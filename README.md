# Junior Django dev application challenge

## Requirements
 Check challenge requirements in *requirements* folder. Don't expect perfection (especially regarding the frontend side and git) though.

## Try online
Go to https://datagen-challenge.herokuapp.com/ (give a minute if stalled - Heroku bootup)
and use the next credentials:  
username: *preview*  
login: *githubtest*

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
