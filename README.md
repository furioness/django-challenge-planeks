[![CI](https://github.com/furioness/django-challenge-planeks/actions/workflows/CI.yml/badge.svg?branch=master)](https://github.com/furioness/django-challenge-planeks/actions/workflows/CI.yml)
[![CodeQL](https://github.com/furioness/django-challenge-planeks/actions/workflows/codeql.yml/badge.svg?branch=master)](https://github.com/furioness/django-challenge-planeks/actions/workflows/codeql.yml)
[![Heroku Deployment](https://github.com/furioness/django-challenge-planeks/actions/workflows/deploy_to_heroku.yml/badge.svg?branch=master)](https://github.com/furioness/django-challenge-planeks/actions/workflows/deploy_to_heroku.yml)
![Coverage](https://img.shields.io/badge/dynamic/xml?label=Coverage%20%28Master%29&prefix=branch-rate%3A%20&query=coverage%2F%40branch-rate&url=https%3A%2F%2Fraw.githubusercontent.com%2Ffurioness%2Fdjango-challenge-planeks%2Fmaster%2F.coverage%2Fcoverage_public.xml "Coverage for Master branch")
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
![Wakatime](https://wakatime.com/badge/user/43ad3009-1842-4a4f-a7fa-e8332aeecd33/project/8209bb54-1f75-4b08-8ea1-eeaa06678f8f.svg "Time in an IDE.")


# Junior Django Developer application challenge
A Django application for generating dummy data by user-defined schemas with arbitrary fields.

## Requirements
 Check challenge requirements in the *requirements* folder. Don't expect perfection (especially regarding the frontend side and git), yet there is some decency.

Also, check [Tasks](https://github.com/furioness/django-challenge-planeks/projects/1) in the Projects tab for the planned tasks.

## Try online
Go to https://datagen-challenge.herokuapp.com/ (give a minute if stalled - Heroku bootup)
and use the next **credentials**:  
**username**: *preview*  
**password**: *githubtest*

## Local run setup
1. Run `docker compose up`
2. `export DJANGO_SETTINGS_MODULE=config.settings.local_docker` 

3. run `worker celery --workdir datagen -A config worker -l INFO`
or `export WORKER_LOCAL=True` to call celery task as `run()` (inprocess) instead of `delay()`
### Git hooks for development setup
Check the content of the `Makefile` and `pre-commit`. Run `make add_git_hooks` and then import somewhere (in user wide environment variables (as hooks often are run outside of IDE environment scope or in `/.env`) Git Guardian key as described [here](https://docs.gitguardian.com/internal-repositories-monitoring/integrations/git_hooks/pre_commit#global-pre-commit-hook).

## Heroku deployment
There is no `requirements.txt`, so to upload to Heroku: **add [poetry build pack](https://github.com/moneymeets/python-poetry-buildpack)** 
Then add services and their credentials to environment variables (check settings.heroku module):
- Heroku CloudAMQP addon or whatever for RabbitMQ
- PostgreSQL URI (Heroku provides a free addon)
- Amazon S3 ([walkthrough](https://testdriven.io/blog/storing-django-static-and-media-files-on-amazon-s3/)) for storing static files and generated datasets (privately)

## Why there are so much code
1) Requirement that different fields can have different parameters. 
2) I wanted to use Django form validators, so I could have error handling for free.
3) Just a few days before I experimented with Faker, so had an idea that there could be a hundred different fields with different parameters (and even different languages). YAGNI...

Having the first two aspects, I needed to have a separate form/model (whatever entity) for handling each field. So my first solution was to use multiple forms for validation and JSON field for storage https://github.com/furioness/django-challenge-planeks/tree/old_JSON_fields - a relatively simple solution. 

Later, I got feedback that is better to store those fields in separate models, and there is too much code for such a task. 

Got it! Now we have an even more complex solution :)

But what they probably meant is just to have a single model for storing all fields with all required parameters (I eventually searched GitHub for other solutions). That indeed is much more simple, but I never thought about it because of the third aspect.
