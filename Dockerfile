FROM ubuntu:xenial as openedx
MAINTAINER devops@edx.org

RUN apt-get update && apt-get upgrade -qy && apt-get install language-pack-en locales git python3.5 python3-pip libmysqlclient-dev libssl-dev python3.5-dev -qy && \
  pip3 install --upgrade pip setuptools && \
  rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/pip3 /usr/bin/pip
RUN ln -s /usr/bin/python3 /usr/bin/python

RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
ENV CREDENTIALS_CFG /edx/etc/credentials.yml
ENV DJANGO_SETTINGS_MODULE credentials.settings.production

EXPOSE 8150

WORKDIR /edx/app/credentials

COPY requirements/base.txt /edx/app/credentials/requirements/base.txt

RUN pip install -r requirements/base.txt

RUN mkdir -p /edx/var/log

RUN useradd -m --shell /bin/false app
USER app

# Gunicorn 19 does not log to stdout or stderr by default. Once we are past gunicorn 19, the logging to STDOUT need not be specified.
CMD gunicorn --workers=2 -c /edx/app/credentials/credentials/docker_gunicorn_configuration.py --log-file - --max-requests=1000 credentials.wsgi:application

COPY . /edx/app/credentials

FROM openedx as edx.org
RUN pip install newrelic
CMD newrelic-admin run-program gunicorn --workers=2 -c /edx/app/credentials/credentials/docker_gunicorn_configuration.py --log-file - --max-requests=1000 credentials.wsgi:application
