# Image for testing outside of CI. Instead of using the ansible generated base image,
# this will run similar to CI in that it is a base Ubuntu image with minimal packages
# installed on top.

FROM ubuntu:20.04 as dev
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

WORKDIR /edx/app/credentials

