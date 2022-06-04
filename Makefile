.PHONY: coverage

docker:
	docker compose up

test_fast:
	python -Wa manage.py test datagen --settings=config.settings.test --shuffle --failfast --parallel --noinput --keepdb --verbosity=0

coverage:
	coverage erase
	coverage run
	coverage combine
	coverage xml
	coverage html

run: 
	./manage.py runserver
	
celery:
	celery --workdir datagen -A config worker -l INFO

add_git_hooks:
	cp pre-commit ./.git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit

format:
	black .
