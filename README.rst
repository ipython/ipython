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

Officially, IPython requires Python version 2.6, 2.7, or 3.1 and above.


Instant running
===============

You can run IPython from this directory without even installing it system-wide
by typing at the terminal::

   $ python ipython.py


Development installation
========================

If you want to hack on certain parts, e.g. the IPython notebook, in a clean
environment (such as a virtualenv) you can use ``pip`` to grab the necessary
dependencies quickly::

   $ pip install -e .[notebook]

This installs the necessary packages and symlinks IPython into your current
environment so that you can work on your local repo copy and run it from anywhere::

   $ ipython notebook

The same process applies for other parts, such as the qtconsole (the
``extras_require`` attribute in the setup.py file lists all the possibilities).
