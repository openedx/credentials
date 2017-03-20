#!/bin/bash -xe
. /edx/app/credentials/venvs/credentials/bin/activate
. /edx/app/credentials/nodeenvs/credentials/bin/activate

apt update
apt install -y gettext firefox xvfb

cd /edx/app/credentials/credentials
export PATH=$PATH:$PWD/node_modules/.bin

make requirements

# Check if translation files are up-to-date
make validate_translations

make clean_static
make static -e DJANGO_SETTINGS_MODULE="credentials.settings.test"
xvfb-run make validate
