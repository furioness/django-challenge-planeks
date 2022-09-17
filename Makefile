.PHONY: coverage

docker:
	docker compose up -d

prepare_rabbitmq_guest_permissions:
	docker exec datagen__rabbitmq rabbitmqctl add_vhost testing
	docker exec datagen__rabbitmq rabbitmqctl set_permissions --vhost testing guest ".*" ".*" ".*"


test_fast: docker
	python -Wa manage.py test datagen --settings=config.settings.test --failfast --parallel --noinput --verbosity=0

coverage: docker
	coverage erase
	coverage run
	coverage combine
	coverage xml
	coverage html

run: docker
	./manage.py runserver
	
celery: docker
	celery --workdir datagen -A config worker -l INFO

add_git_hooks:
	cp pre-commit ./.git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit

format:
	black .

mypy:
	mypy .
