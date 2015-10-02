# Installs IPython from the current branch
# Another Docker container should build from this one to get services like the notebook

FROM ubuntu:14.04

MAINTAINER IPython Project <ipython-dev@scipy.org>

ENV DEBIAN_FRONTEND noninteractive

# Not essential, but wise to set the lang
# Note: Users with other languages should set this in their derivative image
ENV LANGUAGE en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8

# Python binary dependencies, developer tools
RUN apt-get update && apt-get install -y -q \
    build-essential \
    curl \
    language-pack-en \
    make \
    gcc \
    zlib1g-dev \
    git \
    python \
    python-dev \
    python3-dev \
    python-sphinx \
    python3-sphinx \
    libzmq3-dev \
    sqlite3 \
    libsqlite3-dev \
    pandoc \
    libcurl4-openssl-dev \
    nodejs \
    nodejs-legacy \
    npm

# Install the recent pip release
RUN curl -O https://bootstrap.pypa.io/get-pip.py \
 && python2 get-pip.py \
 && python3 get-pip.py \
 && rm get-pip.py

# In order to build from source, need less
RUN npm install -g 'less@<3.0'

RUN pip install invoke

RUN mkdir -p /srv/
WORKDIR /srv/
ADD . /srv/ipython
WORKDIR /srv/ipython/
RUN chmod -R +rX /srv/ipython

# .[all] only works with -e, so use file://path#egg
# Can't use -e because ipython2 and ipython3 will clobber each other
RUN pip2 install file:///srv/ipython#egg=ipython[all]
RUN pip3 install file:///srv/ipython#egg=ipython[all]

# install kernels
RUN python2 -m IPython kernelspec install-self
RUN python3 -m IPython kernelspec install-self

WORKDIR /tmp/

RUN iptest2
RUN iptest3
