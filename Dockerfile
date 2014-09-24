# Just installs IPython from master
# Another Docker container should build from this one to see the Notebook itself

FROM ipython/scipystack

MAINTAINER IPython Project <ipython-dev@scipy.org>

RUN apt-get -y install fabric

RUN mkdir -p /srv/
WORKDIR /srv/
ADD . /srv/ipython
WORKDIR /srv/ipython/
RUN chmod -R +rX /srv/ipython

# .[all] only works with -e, so use file://path#egg
# Can't use -e because ipython2 and ipython3 will clobber each other
RUN pip2 install --upgrade file:///srv/ipython#egg=ipython[all]
RUN pip3 install --upgrade file:///srv/ipython#egg=ipython[all]

# install kernels
RUN python2 -m IPython kernelspec install-self --system
RUN python3 -m IPython kernelspec install-self --system

