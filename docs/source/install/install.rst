IPython requires Python 2.7 or ≥ 3.3.

.. seealso::

   `Installing Jupyter <http://jupyter.readthedocs.org/en/latest/install.html>`__
     The Notebook, nbconvert, and many other former pieces of IPython are now
     part of Project Jupyter.


Quickstart
==========

If you have :mod:`pip`,
the quickest way to get up and running with IPython is:

.. code-block:: bash

    $ pip install ipython

To use IPython with notebooks or the Qt console, you should also install
``jupyter``.

To run IPython's test suite, use the :command:`iptest` command:

.. code-block:: bash

    $ iptest


Overview
========

This document describes in detail the steps required to install IPython.
For a few quick ways to get started with package managers or full Python distributions,
see `the install page <http://ipython.org/install.html>`_ of the IPython website.

Please let us know if you have problems installing IPython or any of its dependencies.

IPython and most dependencies can be installed via :command:`pip`.
In many scenarios, this is the simplest method of installing Python packages.
More information about :mod:`pip` can be found on
`its PyPI page <http://pypi.python.org/pypi/pip>`__.


More general information about installing Python packages can be found in
`Python's documentation <http://docs.python.org>`_.


Installing IPython itself
=========================

Given a properly built Python, the basic interactive IPython shell will work
with no external dependencies.  However, some Python distributions
(particularly on Windows and OS X), don't come with a working :mod:`readline`
module.  The IPython shell will work without :mod:`readline`, but will lack
many features that users depend on, such as tab completion and command line
editing.  If you install IPython with :mod:`pip`,
then the appropriate :mod:`readline` for your platform will be installed.
See below for details of how to make sure you have a working :mod:`readline`.

Installation using pip
----------------------

If you have :mod:`pip`, the easiest way of getting IPython is:

.. code-block:: bash

    $ pip install ipython

That's it.


Installation from source
------------------------

If you don't want to use :command:`pip`, or don't have it installed,
grab the latest stable tarball of IPython `from PyPI
<https://pypi.python.org/pypi/ipython>`__.  Then do the following:

.. code-block:: bash

    $ tar -xzf ipython.tar.gz
    $ cd ipython
    $ python setup.py install

If you are installing to a location (like ``/usr/local``) that requires higher
permissions, you may need to run the last command with :command:`sudo`.


Installing the development version
----------------------------------

It is also possible to install the development version of IPython from our
`Git <http://git-scm.com/>`_ source code repository.  To do this you will
need to have Git installed on your system.  Then do:

.. code-block:: bash

    $ git clone --recursive https://github.com/ipython/ipython.git
    $ cd ipython
    $ python setup.py install

Some users want to be able to follow the development branch as it changes.  If
you have :mod:`pip`, you can replace the last step by:

.. code-block:: bash

    $ pip install -e .

This creates links in the right places and installs the command line script to
the appropriate places. 

Then, if you want to update your IPython at any time, do:

.. code-block:: bash

    $ git pull

.. _dependencies:

Dependencies
============

IPython relies on a number of other Python packages. Installing using a package
manager like pip or conda will ensure the necessary packages are installed. If
you install manually, it's up to you to make sure dependencies are installed.
They're not listed here, because they may change from release to release, so a
static list will inevitably get out of date.

It also has one key non-Python dependency which you may need to install separately.

readline
--------

IPython's terminal interface relies on readline to provide features like tab
completion and history navigation. If you only want to use IPython as a kernel
for Jupyter notebooks and other frontends, you don't need readline.


**On Windows**, to get full console functionality, *PyReadline* is required.
PyReadline is a separate, Windows only implementation of readline that uses
native Windows calls through :mod:`ctypes`. The easiest way of installing
PyReadline is you use the binary installer available `here
<http://pypi.python.org/pypi/pyreadline>`__.

**On OS X**, if you are using the built-in Python shipped by Apple, you will be
missing a proper readline implementation as Apple ships instead a library called
``libedit`` that provides only some of readline's functionality.  While you may
find libedit sufficient, we have occasional reports of bugs with it and several
developers who use OS X as their main environment consider libedit unacceptable
for productive, regular use with IPython.

Therefore, IPython on OS X depends on the :mod:`gnureadline` module.
We will *not* consider completion/history problems to be bugs for IPython if you
are using libedit.

To get a working :mod:`readline` module on OS X, do (with :mod:`pip`
installed):

.. code-block:: bash

    $ pip install gnureadline

.. note::

    Other Python distributions on OS X (such as Anaconda, fink, MacPorts)
    already have proper readline so you likely don't have to do this step.

When IPython is installed with :mod:`pip`,
the correct readline should be installed if you specify the `terminal`
optional dependencies:

.. code-block:: bash

    $ pip install "ipython[terminal]"

**On Linux**, readline is normally installed by default. If not, install it
from your system package manager. If you are compiling your own Python, make
sure you install the readline development headers first.

