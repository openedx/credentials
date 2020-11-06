.DEFAULT_GOAL := help
NODE_BIN=./node_modules/.bin
TOX = ''

.PHONY: help clean production-requirements js-requirements all-requirements requirements isort isort_check pycodestyle \
        quality quality-js test-react tests js-tests static static.dev static.watch migrate up up-dev up-test \
        exec-validate-translations exec-check_translations_up_to_date exec-check_keywords exec-pii_check exec-clean \
        exec-requirements exec-static exec-quality exec-tests exec-accept exec-validate exec-coverage html_coverage \
        shell tail stop down accept extract_translations dummy_translations compile_translations fake_translations \
        pull_translations push_translations detect_changed_source_translations validate_translations \
        check_translations_up_to_date piptools upgrade check_keywords pii_check

ifdef TOXENV
TOX := tox -- #to isolate each tox environment if TOXENV is defined
endif

# Generates a help message. Borrowed from https://github.com/pydanny/cookiecutter-djangopackage.
help: ## Display this help message
	@echo "Please use \`make <target>\` where <target> is one of"
	@awk -F ':.*?## ' '/^[a-zA-Z]/ && NF==2 {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

clean: ## Remove all generated files
	coverage erase
	find . -path '*/__pycache__/*' -delete
	find . -name \*.pyc -o -name \*.pyo -o -name __pycache__ -delete
	rm -rf credentials/assets/ credentials/static/bundles/ credentials/static/jsi18n/ coverage htmlcov test_root/uploads reports
	git clean -fd credentials/conf/locale

production-requirements: piptools ## Install requirements for production
	npm install --no-save
	pip-sync requirements.txt

js-requirements: ## Install frontend requirements
	npm install

all-requirements: piptools ## Install local and prod requirements
	npm install --unsafe-perm ## This flag exists to force node-sass to build correctly on docker. Remove as soon as possible.
	npm install --production --no-save
	pip-sync requirements/all.txt

requirements: piptools ## Install requirements for local development
	npm install --unsafe-perm ## This flag exists to force node-sass to build correctly on docker. Remove as soon as possible.
	pip-sync requirements/dev.txt

isort: ## Run isort to sort imports in all Python files
	isort --recursive --atomic acceptance_tests/ credentials/

isort_check: ## Check that isort has been run
	isort --check-only -rc acceptance_tests/ credentials/

pycodestyle: ## Run pycodestyle
	pycodestyle acceptance_tests credentials *.py

quality: ## Run linters
	make isort_check
	make pycodestyle
	pylint --rcfile=pylintrc acceptance_tests credentials *.py
	make quality-js

quality-js: ## Run JavaScript linter
	$(NODE_BIN)/gulp lint

test-react: ## Run Jest tests for React
	npm run test-react

tests: ## Run tests and generate coverage report
	$(TOX)coverage run -m pytest --ds credentials.settings.test --durations=25
	$(TOX)coverage report
	$(NODE_BIN)/gulp test
	make test-react

js-tests: ## Run tests and generate coverage report
	$(NODE_BIN)/gulp test
	make test-react

static: ## Gather all static assets for production (minimized)
	$(NODE_BIN)/webpack --config webpack.config.js --display-error-details --progress --optimize-minimize
	$(TOX)python manage.py compilejsi18n
	$(TOX)python manage.py collectstatic --noinput -i *.scss

static.dev: ## Gather all static assets for development (not minimized)
	$(NODE_BIN)/webpack --config webpack.config.js --display-error-details --progress
	$(TOX)python manage.py compilejsi18n
	$(TOX)python manage.py collectstatic --noinput -i *.scss

static.watch: ## Gather static assets when they change (not minimized)
	$(NODE_BIN)/webpack --config webpack.config.js --display-error-details --progress --watch
	python manage.py compilejsi18n
	python manage.py collectstatic --noinput -i *.scss

migrate: ## Apply database migrations
	python manage.py migrate --noinput

up: up-dev ## Alias for up-dev

up-dev: ## Bring up services for development
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

up-test: ## Bring up services for testing
	docker-compose -f docker-compose.yml -f docker-compose.travis.yml up -d

exec-validate-translations: ## Check translations on a container
	docker exec -t credentials bash -c 'source /edx/app/credentials/credentials_env && cd /edx/app/credentials/credentials/ && make validate_translations'

exec-check_translations_up_to_date: ## test translations on a container
	docker exec -t credentials bash -c 'source /edx/app/credentials/credentials_env && cd /edx/app/credentials/credentials/ && make check_translations_up_to_date'

exec-check_keywords: ## Scan the Django models in all installed apps in this project for restricted field names
	docker exec -t credentials bash -c 'source /edx/app/credentials/credentials_env && cd /edx/app/credentials/credentials/ && make check_keywords'

exec-pii_check: ## Check for PII annotations on all Django models
	docker exec -t credentials bash -c 'source /edx/app/credentials/credentials_env && cd /edx/app/credentials/credentials/ && make pii_check'

exec-clean: ## Remove all generated files from a container
	docker exec -t credentials bash -c 'source /edx/app/credentials/credentials_env && cd /edx/app/credentials/credentials/ && make clean'

exec-requirements:
	docker exec -t credentials bash -c 'source /edx/app/credentials/credentials_env && cd /edx/app/credentials/credentials/ && make all-requirements'

exec-static: ## Gather static assets on a container
	docker exec -e TOXENV=$(TOXENV) -t credentials bash -c 'source /edx/app/credentials/credentials_env && cd /edx/app/credentials/credentials/ && make static'

exec-quality: ## Run linters on a container
	docker exec -t credentials bash -c 'source /edx/app/credentials/credentials_env && cd /edx/app/credentials/credentials/ && make quality'

exec-tests: ## Run tests on a container
	docker exec -e TOXENV=$(TOXENV) -it credentials bash -c 'source /edx/app/credentials/credentials_env && cd /edx/app/credentials/credentials/ && xvfb-run make tests'

exec-accept: ## Run acceptance tests on a container
	docker exec -it credentials bash -c 'source /edx/app/credentials/credentials_env && cd /edx/app/credentials/credentials/ && make accept'

exec-validate: exec-validate-translations exec-clean exec-static exec-quality exec-tests exec-accept exec-check_keywords exec-pii_check ## Run linters and tests after checking translations and gathering static assets

exec-coverage: ## Generate XML coverage report on a container
	docker exec -t credentials bash -c 'source /edx/app/credentials/credentials_env && cd /edx/app/credentials/credentials/ && coverage xml'

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
	./acceptance_tests/runtests.sh

extract_translations: ## Extract strings to be translated, outputting .po files
	cd credentials && PYTHONPATH=.. i18n_tool extract -v

dummy_translations: ## Generate dummy translation (.po) files
	cd credentials && i18n_tool dummy

compile_translations: ## Compile translation files, outputting .mo files for each supported language
	cd credentials && PYTHONPATH=.. i18n_tool generate

fake_translations: extract_translations dummy_translations compile_translations ## Generate and compile dummy translation files

# This Make target should not be removed since it is relied on by a Jenkins job (`edx-internal/tools-edx-jenkins/translation-jobs.yml`), using `ecommerce-scripts/transifex`.
pull_translations: ## Pull translations from Transifex
	tx pull -af --mode reviewed --minimum-perc=1

# This Make target should not be removed since it is relied on by a Jenkins job (`edx-internal/tools-edx-jenkins/translation-jobs.yml`), using `ecommerce-scripts/transifex`.
push_translations: ## Push source translation files (.po) to Transifex
	tx push -s

detect_changed_source_translations: ## Check if translation files are up-to-date
	cd credentials && i18n_tool changed

validate_translations: ## Test translations files
	cd credentials && i18n_tool validate -v --check-all

check_translations_up_to_date: fake_translations detect_changed_source_translations ## Install fake translations and check if translation files are up-to-date

piptools: 
	pip install -q -r requirements/pip_tools.txt

export CUSTOM_COMPILE_COMMAND = make upgrade
upgrade: piptools ## update the requirements/*.txt files with the latest packages satisfying requirements/*.in
	pip-compile --rebuild --upgrade -o requirements/pip_tools.txt requirements/pip_tools.in
	pip-compile --rebuild --upgrade -o requirements/base.txt requirements/base.in
	pip-compile --rebuild --upgrade -o requirements/test.txt requirements/test.in
	pip-compile --rebuild --upgrade -o requirements/docs.txt requirements/docs.in
	pip-compile --rebuild --upgrade -o requirements/dev.txt requirements/dev.in
	pip-compile --rebuild --upgrade -o requirements/production.txt requirements/production.in
	pip-compile --rebuild --upgrade -o requirements/all.txt requirements/all.in
	# Let tox control the Django version for tests
	grep -e "^django==" requirements/production.txt > requirements/django.txt
	sed '/^[dD]jango==/d' requirements/test.txt > requirements/test.tmp
	mv requirements/test.tmp requirements/test.txt

check_keywords: ## Scan the Django models in all installed apps in this project for restricted field names
	python manage.py check_reserved_keywords --override_file db_keyword_overrides.yml

pii_check: ## Check for PII annotations on all Django models
	DJANGO_SETTINGS_MODULE=credentials.settings.test \
	code_annotations django_find_annotations --config_file .pii_annotations.yml --lint --report --coverage
