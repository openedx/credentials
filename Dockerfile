FROM ubuntu:focal as app

# Warning: This file is experimental.
#
# Short-term goals:
# * Be a suitable replacement for the `edxops/credentials` image in devstack (in progress).
# * Take advantage of Docker caching layers: aim to put commands in order of
#   increasing cache-busting frequency.
# * Related to ^, use no Ansible or Paver.
# Long-term goal:
# * Be a suitable base for production Credentials images. This may not yet be the case.

# Packages installed:
# git; Used to pull in particular requirements from github rather than pypi,
# and to check the sha of the code checkout.

# System requirements

# python3-pip; install pip to install application requirements.txt files
# libssl-dev; # mysqlclient wont install without this.
# libmysqlclient-dev; to install header files needed to use native C implementation for
# MySQL-python for performance gains.
RUN apt-get update && \
apt-get upgrade -qy && apt-get install language-pack-en locales git \
python3.8-dev python3-virtualenv libmysqlclient-dev libssl-dev build-essential wget unzip -qy && \
rm -rf /var/lib/apt/lists/*

# Python is Python3.
RUN ln -s /usr/bin/python3 /usr/bin/python

# language-pack-en locales; ubuntu locale support so that system utilities have a consistent
# language and time zone.
# Use UTF-8.
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8


ARG COMMON_APP_DIR="/edx/app"
ARG CREDENTIALS_APP_DIR="${COMMON_APP_DIR}/credentials"
ENV CREDENTIALS_APP_DIR="${COMMON_APP_DIR}/credentials"
ENV CREDENTIALS_VENV_DIR="${COMMON_APP_DIR}/credentials/venvs/credentials"
ENV CREDENTIALS_CODE_DIR="${CREDENTIALS_APP_DIR}/credentials"
ARG CREDENTIALS_NODEENV_DIR="${COMMON_APP_DIR}/credentials/nodeenvs/credentials"

ENV PATH="$CREDENTIALS_VENV_DIR/bin:$PATH"
ENV CREDENTIALS_NODEENV_DIR "${COMMON_APP_DIR}/credentials/nodeenvs/credentials"

# Working directory will be root of repo.
WORKDIR ${CREDENTIALS_CODE_DIR}

RUN virtualenv -p python3.8 --always-copy ${CREDENTIALS_VENV_DIR}


ENV PATH "${CREDENTIALS_NODEENV_DIR}/bin:$PATH"
# No need to activate credentials venv as it is already in path
RUN pip install nodeenv

RUN nodeenv ${CREDENTIALS_NODEENV_DIR} --node=16.14.0 --prebuilt
RUN npm install -g npm@$8.5.x

# Copy just JS requirements and install them.
COPY package.json package.json
COPY package-lock.json package-lock.json
RUN npm install --production

# Copy just Python requirements & install them.
COPY requirements ${CREDENTIALS_CODE_DIR}/requirements
COPY Makefile ${CREDENTIALS_CODE_DIR}

# credentials service config commands below
RUN pip install -r ${CREDENTIALS_CODE_DIR}/requirements/production.txt

# After the requirements so changes to the code will not bust the image cache
COPY . ${CREDENTIALS_CODE_DIR}/

# placeholder file for the time being unless devstack provisioning scripts need it.
RUN touch ${CREDENTIALS_APP_DIR}/credentials_env
# Expose ports.
EXPOSE 18150

RUN useradd -m --shell /bin/false app

# Install watchman
RUN wget https://github.com/facebook/watchman/releases/download/v2020.08.17.00/watchman-v2020.08.17.00-linux.zip
RUN unzip watchman-v2020.08.17.00-linux.zip
RUN mkdir -p /usr/local/{bin,lib} /usr/local/var/run/watchman
RUN cp watchman-v2020.08.17.00-linux/bin/* /usr/local/bin
RUN cp watchman-v2020.08.17.00-linux/lib/* /usr/local/lib
RUN chmod 755 /usr/local/bin/watchman
RUN chmod 2777 /usr/local/var/run/watchman

# Now install credentials
WORKDIR /edx/app/credentials/credentials

# Copy the requirements explicitly even though we copy everything below
# this prevents the image cache from busting unless the dependencies have changed.
COPY requirements/production.txt /edx/app/credentials/credentials/requirements/production.txt
COPY requirements/pip_tools.txt /edx/app/credentials/credentials/requirements/pip_tools.txt

# Dependencies are installed as root so they cannot be modified by the application user.
RUN pip install -r requirements/pip_tools.txt
RUN pip install -r requirements/production.txt

RUN mkdir -p /edx/var/log

# This line is after the python requirements so that changes to the code will not
# bust the image cache
COPY . /edx/app/credentials/credentials

# Install dependencies in node_modules directory
RUN npm install --no-save
ENV NODE_BIN=/edx/app/credentials/credentials/node_modules
ENV PATH="$NODE_BIN/.bin:$PATH"
# Run webpack
RUN webpack --config webpack.config.js

# Change static folder owner to application user.
RUN chown -R app:app /edx/app/credentials/credentials/credentials/static

# Code is owned by root so it cannot be modified by the application user.
# So we copy it before changing users.
USER app

# Gunicorn 19 does not log to stdout or stderr by default. Once we are past gunicorn 19, the logging to STDOUT need not be specified.
CMD gunicorn --workers=2 --name credentials -c /edx/app/credentials/credentials/credentials/docker_gunicorn_configuration.py --log-file - --max-requests=1000 credentials.wsgi:application


FROM app as dev

# credentials service config commands below
RUN pip install -r ${CREDENTIALS_CODE_DIR}/requirements/dev.txt

ENV DJANGO_SETTINGS_MODULE credentials.settings.devstack

CMD while true; do python ./manage.py runserver 0.0.0.0:18150; sleep 2; done

FROM app as production

ENV DJANGO_SETTINGS_MODULE credentials.settings.production

CMD gunicorn \
    --pythonpath=/edx/app/credentials/credentials \
    --timeout=300 \
    -b 0.0.0.0:18150 \
    -w 2 \
    - credentials.wsgi:application
