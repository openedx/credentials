#!/usr/bin/env bash

# Ansible managed

source /edx/app/credentials/credentials_env
COMMAND=$1

case $COMMAND in
    start)
        /edx/app/supervisor/venvs/supervisor/bin/supervisord -n --configuration /edx/app/supervisor/supervisord.conf
        ;;
    open)
        . /edx/app/credentials/nodeenvs/credentials/bin/activate
        . /edx/app/credentials/venvs/credentials/bin/activate
        cd /edx/app/credentials/credentials

        /bin/bash
        ;;
    exec)
        shift

        . /edx/app/credentials/nodeenvs/credentials/bin/activate
        . /edx/app/credentials/venvs/credentials/bin/activate
        cd "/edx/app/credentials/credentials"

        "$@"
        ;;
    *)
        "$@"
        ;;
esac
