.. image:: https://codecov.io/github/ipython/ipython/coverage.svg?branch=master
    :target: https://codecov.io/github/ipython/ipython?branch=master

.. image:: https://img.shields.io/pypi/dm/IPython.svg           
    :target: https://pypi.python.org/pypi/ipython

.. image:: https://img.shields.io/pypi/v/IPython.svg            
    :target: https://pypi.python.org/pypi/ipython

.. image:: https://img.shields.io/travis/ipython/ipython.svg    
    :target: https://travis-ci.org/ipython/ipython


===========================================
 IPython: Productive Interactive Computing
===========================================

Overview
========

Welcome to IPython.  Our full documentation is available on `ipython.readthedocs.io
<https://ipython.readthedocs.io/en/stable/>`_ and contains information on how to install, use and
contribute to the project.

Officially, IPython requires Python version 3.3 and above.
IPython 5.x is the last IPython version to support Python 2.7.

The Notebook, Qt console and a number of other pieces are now parts of *Jupyter*.
See the `Jupyter installation docs <http://jupyter.readthedocs.io/en/latest/install.html>`__
if you want to use these.




Development and Instant running
===============================

You can find the latest version of the development documentation on `readthedocs
<http://ipython.readthedocs.io/en/latest/>`_.

You can run IPython from this directory without even installing it system-wide
by typing at the terminal::

   $ python -m IPython

Or see the `development installation docs
<http://ipython.readthedocs.io/en/latest/install/install.html#installing-the-development-version>`_
for the latest revision on read the docs.

Documentation and installation instructions for older version of IPython can be
found on the `IPython website <http://ipython.org/documentation.html>`_



IPython requires Python version 3 or above
==========================================

Starting with version 6.0, IPython does not support Python 2.7, 3.0, 3.1, or
3.2.

For a version compatible with Python 2.7, please install the 5.x LTS Long Term
Support version.

If you are encountering this error message you are likely trying to install or
use IPython from source. You need to checkout the remote 5.x branch. If you are
using git the following should work:

  $ git fetch origin
  $ git checkout -b origin/5.x

If you encounter this error message with a regular install of IPython, then you
likely need to update your package manager, for example if you are using `pip`
check the version of pip with

  $ pip --version

You will need to update pip to the version 8.2 or greater. If you are not using
pip, please inquiry with the maintainers of the package for your package
manager.

For more information see one of our blog posts:

    http://blog.jupyter.org/2016/07/08/ipython-5-0-released/

As well as the following Pull-Request for discussion:

    https://github.com/ipython/ipython/pull/9900
