#!/bin/bash -xe
. /edx/app/credentials/venvs/credentials/bin/activate
. /edx/app/credentials/nodeenvs/credentials/bin/activate

apt update
apt install -y gettext

cd /edx/app/credentials/credentials
export PATH=$PATH:$PWD/node_modules/.bin

# Make it so bower can run without sudo.
# https://github.com/GeoNode/geonode/pull/1070
echo '{ "allow_root": true }' > /root/.bowerrc

make requirements

# Check if translation files are up-to-date
make validate_translations

make clean_static
make static -e DJANGO_SETTINGS_MODULE="credentials.settings.test"
make validate
