FROM ubuntu:focal as minimal-system

# Warning: This file is experimental.

ARG DEBIAN_FRONTEND=noninteractive

# Env vars: paver
# We intentionally don't use paver in this Dockerfile, but Devstack may invoke paver commands
# during provisioning. Enabling NO_PREREQ_INSTALL tells paver not to re-install Python
# requirements for every paver command, potentially saving a lot of developer time.
ARG NO_PREREQ_INSTALL='1'

# Env vars: locale
ENV LANG='en_US.UTF-8'
ENV LANGUAGE='en_US:en'
ENV LC_ALL='en_US.UTF-8'

# Env vars: path
ENV VIRTUAL_ENV="/edx/app/credentials/venvs/credentials"
ENV NODE_ENV="/edx/app/credentials/nodeenvs/credentials"
ENV NODE_BIN="/edx/app/credentials/credentials/node_modules"
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"
ENV PATH="$NODE_ENV/bin:$PATH"
ENV PATH="$NODE_BIN/.bin:$PATH"


WORKDIR /edx/app/credentials/credentials

# Create user before assigning any directory ownership to it.
RUN useradd -m --shell /bin/false app

# Use debconf to set locales to be generated when the locales apt package is installed later.
RUN echo "locales locales/default_environment_locale select en_US.UTF-8" | debconf-set-selections
RUN echo "locales locales/locales_to_be_generated multiselect en_US.UTF-8 UTF-8" | debconf-set-selections

# Install requirements that are absolutely necessary
RUN apt-get update && \
    apt-get -y dist-upgrade && \
    apt-get -y install --no-install-recommends \
        python3 \
        python3.8-dev \
        python3.8-venv \
        python3.8 \
        python3.8-minimal \
        libpython3.8 \
        libpython3.8-stdlib \
        libmysqlclient21 \
        libssl1.1 \
        wget \
        unzip \
        locales \
        software-properties-common \
	make \
    && \
    apt-get clean all && \
    rm -rf /var/lib/apt/*

RUN mkdir -p /edx/var/credentials
RUN mkdir -p /edx/etc
RUN chown app:app /edx/var/credentials

# The builder-production stage is a temporary stage that installs required packages and builds the python virtualenv,
# installs nodejs and node_modules. # The built artifacts from this stage are then copied to the base stage.

FROM minimal-system as builder-production

RUN apt-get update && \
    apt-add-repository -y ppa:deadsnakes/ppa && apt-get update && \
    apt-get -y install --no-install-recommends \
        language-pack-en \
        locales\
        curl \
        git \
        git-core \
        pkg-config \
        build-essential \
        libmysqlclient-dev \
        libssl-dev \
    && \
    apt-get clean all && \
    rm -rf /var/lib/apt/*   

# Setup python virtual environment
# It is already 'activated' because $VIRTUAL_ENV/bin was put on $PATH
RUN python3.8 -m venv "${VIRTUAL_ENV}"

# Install python requirements
# Requires copying over requirements files, but not entire repository

COPY requirements/production.txt /edx/app/credentials/credentials/requirements/production.txt
COPY requirements/pip_tools.txt /edx/app/credentials/credentials/requirements/pip_tools.txt

RUN pip install -r requirements/pip_tools.txt
RUN pip install -r requirements/production.txt


# Install node and node modules
RUN pip install nodeenv
RUN nodeenv /edx/app/credentials/nodeenvs/credentials --node=16.14.0 --prebuilt
RUN npm install -g npm@8.5.3

# Copy over remaining parts of repository (including all code)

COPY . .
RUN npm install --no-save
# Run webpack
RUN webpack --config webpack.config.js

# Change static folder owner to application user.
RUN chown -R app:app /edx/app/credentials/credentials/credentials/static

# The builder-development stage is a temporary stage that installs python modules required for development purposes
# The built artifacts from this stage are then copied to the development stage.
FROM builder-production as builder-development
COPY requirements/dev.txt /edx/app/credentials/credentials/requirements/dev.txt
RUN pip install -r /edx/app/credentials/credentials/requirements/dev.txt


# base stage
FROM minimal-system as base

# Copy python virtual environment, nodejs and node_modules
COPY --from=builder-production /edx/app/credentials/venvs/credentials /edx/app/credentials/venvs/credentials
COPY --from=builder-production /edx/app/credentials/nodeenvs/credentials /edx/app/credentials/nodeenvs/credentials
COPY --from=builder-production /edx/app/credentials/credentials/node_modules /edx/app/credentials/credentials/node_modules
COPY --from=builder-production /edx/app/credentials/credentials/credentials/static /edx/app/credentials/credentials/credentials/static

USER app

# Production target
FROM base as production
ENV CREDENTIALS_PLATFORM_SETTINGS='production'
ENV DJANGO_SETTINGS_MODULE="credentials.settings.$CREDENTIALS_PLATFORM_SETTINGS"
EXPOSE 18150
CMD gunicorn \
    -c /edx/app/credentials/credentials/credentials/docker_gunicorn_configuration.py \
    --name credentials \
    --bind=0.0.0.0:18150 \
    --max-requests=1000 \
    --log-file - \
    - credentials.wsgi:application

# Development target
FROM base as development

# Install watchman
RUN wget https://github.com/facebook/watchman/releases/download/v2020.08.17.00/watchman-v2020.08.17.00-linux.zip && \
    unzip watchman-v2020.08.17.00-linux.zip && \
    mkdir -p /usr/local/{bin,lib} /usr/local/var/run/watchman && \
    cp watchman-v2020.08.17.00-linux/bin/* /usr/local/bin && \
    cp watchman-v2020.08.17.00-linux/lib/* /usr/local/lib && \
    chmod 755 /usr/local/bin/watchman && \
    chmod 2777 /usr/local/var/run/watchman

COPY --from=builder-development /edx/app/credentials/venvs/credentials /edx/app/credentials/venvs/credentials

USER root

# Temporary compatibility hack while devstack is supporting both the old `edxops/credentials` image and this image.
# * Add in a dummy ../credentials_env file
RUN touch ../credentials_env

ENV CREDENTIALS_PLATFORM_SETTINGS='devstack'
ENV DJANGO_SETTINGS_MODULE="credentials.settings.$CREDENTIALS_PLATFORM_SETTINGS"
EXPOSE 18150
CMD while true; do python ./manage.py runserver 0.0.0.0:18150; sleep 2; done
