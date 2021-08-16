FROM ubuntu:focal as app
MAINTAINER devops@edx.org


# Packages installed:
# git; Used to pull in particular requirements from github rather than pypi,
# and to check the sha of the code checkout.

# language-pack-en locales; ubuntu locale support so that system utilities have a consistent
# language and time zone.

# python; ubuntu doesnt ship with python, so this is the python we will use to run the application

# python3-pip; install pip to install application requirements.txt files

# libssl-dev; # mysqlclient wont install without this.

# libmysqlclient-dev; to install header files needed to use native C implementation for
# MySQL-python for performance gains.

# wget to download a watchman binary archive

# unzip to unzip a watchman binary archive

# If you add a package here please include a comment above describing what it is used for
RUN apt-get update && \
apt-get install -y software-properties-common && \
apt-add-repository -y ppa:deadsnakes/ppa && apt-get update && \
apt-get upgrade -qy && apt-get install language-pack-en locales git \
python3.8-dev python3.8-venv libmysqlclient-dev libssl-dev build-essential wget unzip -qy && \
rm -rf /var/lib/apt/lists/*

# Create Python env
ENV VIRTUAL_ENV=/edx/app/credentials/venvs/credentials
RUN python3.8 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Create Node env
RUN pip install nodeenv
ENV NODE_ENV=/edx/app/credentials/nodeenvs/credentials
RUN nodeenv $NODE_ENV --node=12.11.1 --prebuilt
ENV PATH="$NODE_ENV/bin:$PATH"
RUN npm install -g npm@6.12.1

RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
ENV DJANGO_SETTINGS_MODULE credentials.settings.production

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

# Code is owned by root so it cannot be modified by the application user.
# So we copy it before changing users.
USER app

# Gunicorn 19 does not log to stdout or stderr by default. Once we are past gunicorn 19, the logging to STDOUT need not be specified.
CMD gunicorn --workers=2 --name credentials -c /edx/app/credentials/credentials/credentials/docker_gunicorn_configuration.py --log-file - --max-requests=1000 credentials.wsgi:application

# This line is after the requirements so that changes to the code will not
# bust the image cache
COPY . /edx/app/credentials/credentials

FROM app as newrelic
RUN pip install newrelic
CMD newrelic-admin run-program gunicorn --workers=2 --name credentials -c /edx/app/credentials/credentials/credentials/docker_gunicorn_configuration.py --log-file - --max-requests=1000 credentials.wsgi:application


# We don't switch back to the app user for devstack because we need devstack users to be
# able to update requirements and generally run things as root.
FROM app as devstack
USER root
RUN pip install -r /edx/app/credentials/credentials/requirements/dev.txt
CMD gunicorn --reload --workers=2 --name credentials -c /edx/app/credentials/credentials/credentials/docker_gunicorn_configuration.py --log-file - --max-requests=1000 credentials.wsgi:application
