# Designed to be run as 
# 
# docker run -it -p 9999:8888 ipython/latest

FROM ipython/scipystack

MAINTAINER IPython Project <ipython-dev@scipy.org>

# Can't directly add the source as it won't have the submodules
RUN mkdir -p /srv/
WORKDIR /srv/
ADD . /srv/ipython
WORKDIR /srv/ipython/

# Installing certain dependencies directly
RUN pip2 install fabric
RUN pip3 install jsonschema jsonpointer fabric

RUN python setup.py submodule

# .[all] only works with -e
# Can't use -e because ipython2 and ipython3 will clobber each other
RUN pip2 install .
RUN pip3 install .
