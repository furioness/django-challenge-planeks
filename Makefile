.PHONY: coverage

docker:
	docker compose up

test_fast:
	./manage.py test datagen --settings=config.settings.test --shuffle --failfast --parallel --noinput --keepdb

coverage:
	coverage erase
	coverage run
	coverage combine
	coverage xml
	coverage html

run:
	./manage.py runserver

add_git_hooks:
	cp pre-commit ./.git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit
