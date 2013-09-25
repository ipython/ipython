===========================================
 IPython: Productive Interactive Computing
===========================================

Overview
========

Welcome to IPython.  Our full documentation is available on `our website
<http://ipython.org/documentation.html>`_; if you downloaded a built source
distribution the ``docs/source`` directory contains the plaintext version of
these manuals.  If you have Sphinx installed, you can build them by typing
``cd docs; make html`` for local browsing.


Dependencies and supported Python versions
==========================================

For full details, see the installation section of the manual.  The basic parts
of IPython only need the Python standard library, but much of its more advanced
functionality requires extra packages.

Officially, IPython requires Python version 2.7, or 3.3 and above.
IPython 1.x is the last IPython version to support Python 2.6 and 3.2.


Instant running
===============

You can run IPython from this directory without even installing it system-wide
by typing at the terminal::

   $ python -m IPython


Development installation
========================

If you want to hack on certain parts, e.g. the IPython notebook, in a clean
environment (such as a virtualenv) you can use ``pip`` to grab the necessary
dependencies quickly::

   $ git clone --recursive https://github.com/ipython/ipython.git
   $ cd ipython
   $ pip install -e ".[notebook]"

This installs the necessary packages and symlinks IPython into your current
environment so that you can work on your local repo copy and run it from anywhere::

   $ ipython notebook

The same process applies for other parts, such as the qtconsole (the
``extras_require`` attribute in the setup.py file lists all the possibilities).

Git Hooks and Submodules
************************

IPython now uses git submodules to ship its javascript dependencies.
If you run IPython from git master, you may need to update submodules once in a while with::

    $ git submodule update

or::

    $ python setup.py submodule

We have some git hooks for helping keep your submodules always in sync,
see our ``git-hooks`` directory for more info.
