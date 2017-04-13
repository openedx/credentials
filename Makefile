.DEFAULT_GOAL := tests
NODE_BIN=./node_modules/.bin
APP_DIR=cd /edx/app/credentials/credentials/
SOURCE_VENV=. /edx/app/credentials/venvs/credentials/bin/activate
SOURCE_NODEENV=. /edx/app/credentials/nodeenvs/credentials/bin/activate

.PHONY: requirements

# Generates a help message. Borrowed from https://github.com/pydanny/cookiecutter-djangopackage.
help: ## Display this help message
	@echo "Please use \`make <target>\` where <target> is one of"
	@perl -nle'print $& if m{^[\.a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

clean: ## Remove all generated files
	coverage erase
	rm -rf credentials/assets/ credentials/static/bundles/ coverage htmlcov test_root/uploads

production-requirements: ## Install requirements for production
	npm install --production
	pip install -r requirements.txt

requirements: ## Install requirements for local development
	npm install
	pip install -r requirements/local.txt

quality: ## Run linters
	isort --check-only --recursive acceptance_tests/ credentials/
	pep8 --config=.pep8 acceptance_tests credentials *.py
	pylint --rcfile=pylintrc acceptance_tests credentials *.py
	$(NODE_BIN)/gulp lint

tests: ## Run tests and generate coverage report
	coverage run -m pytest
	coverage report
	$(NODE_BIN)/gulp test

static: ## Gather all static assets for production (mimized)
	$(NODE_BIN)/webpack --config webpack.config.js --display-error-details --progress --optimize-minimize
	python manage.py collectstatic --noinput -i *.scss

static.dev: ## Gather all static assets for development (not minimized)
	$(NODE_BIN)/webpack --config webpack.config.js --display-error-details --progress

static.watch: ## Gather static assets when they change (not minimized)
	$(NODE_BIN)/webpack --config webpack.config.js --display-error-details --progress --watch

migrate: ## Apply database migrations
	python manage.py migrate --noinput

up: up-dev ## Alias for up-dev

up-dev: ## Bring up services for development
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

up-test: ## Bring up services for testing
	docker-compose -f docker-compose.yml -f docker-compose.test.yml up -d

exec-requirements: ## Install requirements on a container
	docker exec -t credentials bash -c '$(SOURCE_VENV) && $(SOURCE_NODEENV) && apt update && apt install -y gettext firefox xvfb && $(APP_DIR) && make requirements'

exec-validate-translations: ## Check translations on a container
	docker exec -t credentials bash -c '$(SOURCE_VENV) && $(APP_DIR) && make validate_translations'

exec-clean: ## Remove all generated files from a container
	docker exec -t credentials bash -c '$(SOURCE_VENV) && $(APP_DIR) && make clean'

exec-static: ## Gather static assets on a container
	docker exec -t credentials bash -c '$(SOURCE_VENV) && $(SOURCE_NODEENV) && $(APP_DIR) && make static'

exec-quality: ## Run linters on a container
	docker exec -t credentials bash -c '$(SOURCE_VENV) && $(SOURCE_NODEENV) && $(APP_DIR) && make quality'

exec-tests: ## Run tests on a container
	docker exec -it credentials bash -c '$(SOURCE_VENV) && $(SOURCE_NODEENV) && $(APP_DIR) && xvfb-run make tests'

exec-validate: exec-validate-translations exec-clean exec-static exec-quality exec-tests ## Run linters and tests after checking translations and gathering static assets

exec-coverage: ## Generate XML coverage report on a container
	docker exec -t credentials bash -c '$(SOURCE_VENV) && $(APP_DIR) && coverage xml'

html_coverage: ## Generate and view HTML coverage report
	coverage html && open htmlcov/index.html

shell: ## Run a shell on a credentials container
	docker exec -it credentials env TERM=$(TERM) /edx/app/credentials/devstack.sh open

tail: ## View logs from services running in detached mode
	docker-compose logs --follow

stop: ## Stop all services
	docker-compose stop

down: ## Bring down all services and remove associated resources
	docker-compose down

accept: ## Run acceptance tests
	pytest acceptance_tests

extract_translations: ## Extract strings to be translated, outputting .mo files
	python manage.py makemessages -l en -v1 -d django --ignore="docs/*" --ignore="credentials/assets/*" --ignore="node_modules/*" --ignore="credentials/static/bundles/*"

dummy_translations: ## Generate dummy translation (.po) files
	cd credentials && i18n_tool dummy

compile_translations: ## Compile translation files, outputting .po files for each supported language
	python manage.py compilemessages

fake_translations: extract_translations dummy_translations compile_translations ## Generate and compile dummy translation files

pull_translations: ## Pull translations from Transifex
	tx pull -af --mode reviewed

detect_changed_source_translations: ## Check if translation files are up-to-date
	cd credentials && i18n_tool changed

validate_translations: fake_translations detect_changed_source_translations ## Install fake translations and check if translation files are up-to-date
