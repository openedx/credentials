# Image for testing outside of CI. Instead of using the ansible generated base image,
# this will run similar to CI in that it is a base Ubuntu image with minimal packages
# installed on top.

FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    firefox \
    xvfb \
    build-essential \
    python3.8-dev \
    python3-pip \
    libmysqlclient-dev \
    gettext \
    git \
    curl
RUN curl -sL https://deb.nodesource.com/setup_lts.x | bash - && apt-get install -y nodejs  # NOTE: This installs node LTS which is v14 currently
RUN ln -s /usr/bin/pip3 /usr/bin/pip
RUN ln -s /usr/bin/python3 /usr/bin/python
RUN mkdir -p /edx/app/credentials/
WORKDIR /edx/app/credentials
COPY ./requirements/ /edx/app/credentials/requirements/
COPY ./package.json /edx/app/credentials/package.json
COPY ./package-lock.json /edx/app/credentials/package-lock.json
COPY ./Makefile /edx/app/credentials/Makefile
RUN make requirements
