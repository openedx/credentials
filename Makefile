.DEFAULT_GOAL := test
NODE_BIN=$(CURDIR)/node_modules/.bin

.PHONY: clean compile_translations dummy_translations extract_translations fake_translations help html_coverage \
	migrate pull_translations push_translations quality requirements test update_translations validate \
	production-requirements static static.dev static.watch

help:
	@echo "Please use \`make <target>\` where <target> is one of"
	@echo "  clean                      delete generated byte code and coverage reports"
	@echo "  compile_translations       compile translation files, outputting .po files for each supported language"
	@echo "  dummy_translations         generate dummy translation (.po) files"
	@echo "  extract_translations       extract strings to be translated, outputting .mo files"
	@echo "  fake_translations          generate and compile dummy translation files"
	@echo "  help                       display this help message"
	@echo "  html_coverage              generate and view HTML coverage report"
	@echo "  migrate                    apply database migrations"
	@echo "  production-requirements    install requirements for production"
	@echo "  pull_translations          pull translations from Transifex"
	@echo "  push_translations          push source translation files (.po) from Transifex"
	@echo "  quality                    run PEP8 and Pylint"
	@echo "  requirements               install requirements for local development"
	@echo "  serve                      serve Credentials at 0.0.0.0:8150"
	@echo "  static                     gather all static assets for production (mimized)"
	@echo "  static.dev                 gather all static assets for development (not minimized)"
	@echo "  static.watch               watch the assets, and automatically gather all static assets for development (not minimized)"
	@echo "  clean_static               remove all generated static files"
	@echo "  test                       run tests and generate coverage report"
	@echo "  validate                   run tests and quality checks"
	@echo "  start-devstack             run a local development copy of the server"
	@echo "  open-devstack              open a shell on the server started by start-devstack"
	@echo "  pkg-devstack               build the credentials image from the latest configuration and code"
	@echo "  make accept                run acceptance tests"
	@echo "  detect_changed_source_translations       check if translation files are up-to-date"
	@echo "  validate_translations      install fake translations and check if translation files are up-to-date"
	@echo ""

clean:
	find . -name '*.pyc' -delete
	coverage erase
	rm -rf coverage htmlcov test_root/uploads

clean_static:
	rm -rf credentials/assets/ credentials/static/bundles/

production-requirements:
	npm install --production
	pip install -r requirements.txt

requirements:
	npm install
	pip install -r requirements/local.txt

test: clean
	coverage run -m pytest
	coverage report

quality:
	isort --check-only --recursive acceptance_tests/ credentials/
	pep8 --config=.pep8 acceptance_tests credentials *.py
	pylint --rcfile=pylintrc acceptance_tests credentials *.py
	$(NODE_BIN)/gulp lint

static:
	$(NODE_BIN)/webpack --config webpack.config.js --display-error-details --progress --optimize-minimize
	python manage.py collectstatic --noinput -i *.scss

static.dev:
	$(NODE_BIN)/webpack --config webpack.config.js --display-error-details --progress

static.watch:
	$(NODE_BIN)/webpack --config webpack.config.js --display-error-details --progress --watch

serve:
	python manage.py runserver 0.0.0.0:8150

validate: quality test

migrate:
	python manage.py migrate

html_coverage:
	coverage html && open htmlcov/index.html

extract_translations:
	python manage.py makemessages -l en -v1 -d django --ignore="docs/*" --ignore="credentials/assets/*" --ignore="node_modules/*" --ignore="credentials/static/bundles/*"

dummy_translations:
	cd credentials && i18n_tool dummy

compile_translations:
	python manage.py compilemessages

fake_translations: extract_translations dummy_translations compile_translations

pull_translations:
	tx pull -af --mode reviewed

push_translations:
	tx push -s

start-devstack:
	docker-compose up

open-devstack:
	docker-compose up -d
	docker exec -it credentials env TERM=$(TERM) /edx/app/credentials/devstack.sh open

pkg-devstack:
	docker build -t credentials:latest -f docker/build/credentials/Dockerfile git://github.com/edx/configuration

accept:
	nosetests --with-ignore-docstrings -v acceptance_tests

detect_changed_source_translations:
	cd credentials && i18n_tool changed

validate_translations: fake_translations detect_changed_source_translations
