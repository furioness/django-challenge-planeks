docker:
	docker compose up

test_fast:
	run manage.py test datagen --settings=config.settings.test --shuffle --failfast --parallel

test:
	coverage run manage.py test datagen --settings=config.settings.test  --shuffle
	coverage xml
	coverage html

run:
	./manage.py runserver

add_git_hooks:
	cp pre-commit ./.git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit
