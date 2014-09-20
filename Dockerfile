# Just installs IPython from master
# Another Docker container should build from this one to see the Notebook itself

FROM ipython/scipystack

MAINTAINER IPython Project <ipython-dev@scipy.org>

RUN mkdir -p /srv/
WORKDIR /srv/
ADD . /srv/ipython
WORKDIR /srv/ipython/

# Installing certain dependencies directly
RUN pip2 install fabric
RUN pip3 install jsonschema jsonpointer fabric

# .[all] only works with -e
# Can't use -e because ipython2 and ipython3 will clobber each other
RUN pip2 install .
RUN pip3 install .
