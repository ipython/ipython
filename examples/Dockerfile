# 
# This Docker container brings up an entire environment with (almost) all of the dependencies required by the example notebooks.
# 
# To use this directly, run
#   docker run -p 8888:8888 ipython/examples
#

FROM ipython/scipyserver

MAINTAINER IPython Project <ipython-dev@scipy.org>

# Requirements for some of the Example notebooks
RUN apt-get build-dep -y mpi4py
RUN pip install scikit-image vincent dill networkx mpi4py

ADD . /notebooks/
