# Installs IPython from the current branch
# Other Docker images should build from this one to get services like the notebook

FROM ubuntu:14.04

MAINTAINER IPython Project <ipython-dev@scipy.org>

# Not essential, but wise to set the lang
# Note: Users with other languages should set this in their derivative image
ENV LANGUAGE en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8

# Python binary dependencies, developer tools
RUN apt-get update -qq \
 && DEBIAN_FRONTEND=noninteractive apt-get install -yq --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        git \
        language-pack-en \
        libcurl4-openssl-dev \
        libsqlite3-dev \
        libzmq3-dev \
        nodejs \
        nodejs-legacy \
        npm \
        pandoc \
        python \
        python-dev \
        python3-dev \
        python-sphinx \
        python3-sphinx \
        sqlite3 \
        zlib1g-dev \
 && rm -rf /var/lib/apt/lists/*

# Install the recent pip release
RUN curl -O https://bootstrap.pypa.io/get-pip.py \
 && python2 get-pip.py \
 && python3 get-pip.py \
 && rm get-pip.py

# In order to build from source, need less
RUN npm install -g 'less@<3.0' \
 && npm cache clean

RUN pip install invoke

RUN mkdir -p /srv/
WORKDIR /srv/
ADD . /srv/ipython
WORKDIR /srv/ipython/
RUN chmod -R +rX /srv/ipython

# .[all] only works with -e, so use file://path#egg
# Can't use -e because ipython2 and ipython3 will clobber each other
RUN pip2 install --no-cache-dir file:///srv/ipython#egg=ipython[all]
RUN pip3 install --no-cache-dir file:///srv/ipython#egg=ipython[all]

# install kernels
RUN python2 -m IPython kernelspec install-self
RUN python3 -m IPython kernelspec install-self

WORKDIR /tmp/

RUN iptest2
RUN iptest3
