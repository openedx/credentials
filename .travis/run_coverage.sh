#!/bin/bash -xe
. /edx/app/credentials/venvs/credentials/bin/activate
cd /edx/app/credentials/credentials
coverage xml
