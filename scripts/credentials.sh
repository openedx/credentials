#!/usr/bin/env bash

# Ansible managed



export EDX_REST_API_CLIENT_NAME="default_env-default_deployment-credentials"

source /edx/app/credentials/credentials_env

exec /edx/app/credentials/venvs/credentials/bin/gunicorn -c /edx/app/credentials/credentials_gunicorn.py --reload credentials.wsgi:application
