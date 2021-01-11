.DEFAULT_GOAL := help
NODE_BIN=./node_modules/.bin
TOX = ''

.PHONY: help clean \
	production-requirements all-requirements requirements piptools upgrade \
	quality quality_fix isort isort_check format format_check quality-js \
	tests js-tests accept \
	static static.dev static.watch \
	extract_translations dummy_translations compile_translations fake_translations pull_translations push_translations \
	detect_changed_source_translations validate_translations check_translations_up_to_date \
	check_keywords pii_check coverage \
	acceptance_tests_suite quality_and_translations_tests_suite unit_tests_suite

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

### Requirements commands ###

production-requirements: piptools ## Install requirements for production
	npm install --no-save
	pip-sync requirements/production.txt

all-requirements: piptools ## Install local and prod requirements
	npm install
	npm install --production --no-save
	pip-sync requirements/all.txt

requirements: piptools ## Install requirements for local development
	npm install
	pip-sync requirements/dev.txt

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

### Quality commands ###

quality: isort_check quality-js format_check ## Run linters
	pylint --rcfile=pylintrc acceptance_tests credentials *.py

quality_fix: isort format

isort: ## Run isort to sort imports in all Python files
	isort --recursive --atomic acceptance_tests/ credentials/

isort_check: ## Check that isort has been run
	isort --check-only acceptance_tests/ credentials/

format: ## format code
	black .

format_check: ## check that code is formatted correctly
	black --check .

quality-js: ## Run JavaScript linter
	$(NODE_BIN)/gulp lint

### Testing commands ###

tests: ## Run tests and generate coverage report
	$(TOX)coverage run -m pytest --ds credentials.settings.test --durations=25
	$(TOX)coverage report
	make js-tests

js-tests: ## Run javascript tests
	$(NODE_BIN)/gulp test
	npm run test-react

# Requires locally installed software (firefox / xvfb). Easiest to run using `acceptance_tests_suite` command at the bottom
accept: ## Run acceptance tests
	./acceptance_tests/runtests.sh

### Frontend commands ###
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

### Translation commands

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

### Additonal linting commands

check_keywords: ## Scan the Django models in all installed apps in this project for restricted field names
	python manage.py check_reserved_keywords --override_file db_keyword_overrides.yml

pii_check: ## Check for PII annotations on all Django models
	DJANGO_SETTINGS_MODULE=credentials.settings.test \
	code_annotations django_find_annotations --config_file .pii_annotations.yml --lint --report --coverage

coverage:
	coverage xml

### Local testing suite commands ###

build_test_image: # Builds Docker image used for testing so devs don't need to install requirements locally (useful for firefox / xvfb)
	docker build -t credentials:local -f Dockerfile-testing .

# This should be ran locally, not inside of the devstack container
acceptance_tests_suite: build_test_image
	docker run -e "TERM=xterm-256color" credentials:local bash -c 'cd /edx/app/credentials/ && make static && make accept'

# This should be ran locally, not inside of the devstack container
quality_and_translations_tests_suite: build_test_image
	docker run -e "TERM=xterm-256color" credentials:local bash -c 'cd /edx/app/credentials/ && make check_translations_up_to_date && make validate_translations && make quality && make check_keywords && make pii_check'

# This should be ran locally, not inside of the devstack container
unit_tests_suite: build_test_image
	docker run -e "TERM=xterm-256color" credentials:local bash -c 'cd /edx/app/credentials/ && make static && make tests && make coverage'
