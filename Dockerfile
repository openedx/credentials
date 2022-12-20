FROM ubuntu:focal as app

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
ENV CREDENTIALS_NODEENV_BIN "${CREDENTIALS_NODEENV_DIR}/bin"
ENV CREDENTIALS_NODE_MODULES_DIR "${CREDENTIALS_CODE_DIR}}/node_modules"
ENV CREDENTIALS_NODE_BIN "${CREDENTIALS_NODE_MODULES_DIR}/.bin"

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
