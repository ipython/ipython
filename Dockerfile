# DEPRECATED: You probably want jupyter/notebook

FROM jupyter/notebook

MAINTAINER IPython Project <ipython-dev@scipy.org>

ONBUILD RUN echo "ipython/ipython is deprecated, use jupyter/notebook" >&2
