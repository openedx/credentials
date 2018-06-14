# docker build . -t edxops/credentials:devstack-slim

FROM edxops/python:3.5
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE credentials.settings.devstack
ENV ENABLE_DJANGO_TOOLBAR 1

WORKDIR /edx/app/credentials/credentials

# Iceweasel is the Debian name for Firefox
RUN apt-get update && apt-get install -y \
    iceweasel \
    xvfb
