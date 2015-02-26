IPython requires Python 2.7 or ≥ 3.3.

.. note::

    If you need to use Python 2.6 or 3.2, you can find IPython 1.x
    `here <http://archive.ipython.org/release/>`__,
    or get it with pip::
    
        pip install 'ipython<2'


Quickstart
==========

If you have :mod:`pip`,
the quickest way to get up and running with IPython is:

.. code-block:: bash

    $ pip install "ipython[all]"

This will download and install IPython and its main optional dependencies for the notebook,
qtconsole, tests, and other functionality.
Some dependencies (Qt, PyQt for the QtConsole, pandoc for nbconvert) are not pip-installable,
and will not be pulled in by pip.

To run IPython's test suite, use the :command:`iptest` command:

.. code-block:: bash

    $ iptest


Overview
========

This document describes in detail the steps required to install IPython,
and its various optional dependencies.
For a few quick ways to get started with package managers or full Python distributions,
see `the install page <http://ipython.org/install.html>`_ of the IPython website.

IPython is organized into a number of subpackages, each of which has its own dependencies.
All of the subpackages come with IPython, so you don't need to download and
install them separately.  However, to use a given subpackage, you will need to
install all of its dependencies.

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
grab the latest stable build of IPython from `here
<http://ipython.org/download.html>`_.  Then do the following:

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

IPython now uses git submodules to ship its javascript dependencies. If you run 
IPython from git master, you may need to update submodules once in a while with:

.. code-block:: bash

    $ git submodule update

or

.. code-block:: bash

    $ python setup.py submodule

Another option is to copy `git hooks <https://github.com/ipython/ipython/tree/master/git-hooks>`_
to your ``./git/hooks/`` directory to ensure that your submodules are up to date on each pull.


Basic optional dependencies
===========================

There are a number of basic optional dependencies that most users will want to
get.  These are:

* readline (for command line editing, tab completion, etc.)
* nose (to run the IPython test suite)
* mock (Python < 3, also for tests)

If you are comfortable installing these things yourself, have at it, otherwise
read on for more details.

IPython uses several other modules, such as pexpect_ and path.py, if they are
installed on your system, but it can also use bundled versions from
:mod:`IPython.external`, so there's no need to install them separately.

readline
--------

As indicated above, on Windows, to get full functionality in the console
version of IPython, PyReadline is needed.
PyReadline is a separate, Windows only implementation of readline that uses
native Windows calls through :mod:`ctypes`. The easiest way of installing
PyReadline is you use the binary installer available `here
<http://pypi.python.org/pypi/pyreadline>`__.

On OS X, if you are using the built-in Python shipped by Apple, you will be
missing a proper readline implementation as Apple ships instead a library called
``libedit`` that provides only some of readline's functionality.  While you may
find libedit sufficient, we have occasional reports of bugs with it and several
developers who use OS X as their main environment consider libedit unacceptable
for productive, regular use with IPython.

Therefore, IPython on OS X depends on the :mod:`gnureadline` module.
We will *not* consider completion/history problems to be bugs for IPython if you are using libedit.

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


nose
----

To run the IPython test suite you will need the :mod:`nose` package.  Nose
provides a great way of sniffing out and running all of the IPython tests.  The
simplest way of getting nose is to use :command:`pip`:

.. code-block:: bash

    $ pip install nose

Another way of getting this is to do:

.. code-block:: bash

    $ pip install "ipython[test]"

For more installation options, see the `nose website
<http://somethingaboutorange.com/mrl/projects/nose/>`_.  

Once you have nose installed, you can run IPython's test suite using the
iptest command:

.. code-block:: bash

    $ iptest

Dependencies for IPython.parallel (parallel computing)
======================================================

IPython's inter-process communication uses the PyZMQ_ bindings for the ZeroMQ_ messaging library.
This is the only dependency for :mod:`IPython.parallel`.

Shortcut:

.. code-block:: bash

    pip install "ipython[parallel]"

or manual

.. code-block:: bash

    pip install pyzmq

PyZMQ provides wheels for current Python on OS X and Windows, so installing pyzmq will typically not require compilation.

IPython.parallel can use SSH tunnels, which require paramiko_ on Windows.

Dependencies for the IPython Qt console
=======================================

pyzmq_, pygments_, PyQt_ (or PySide_)

Shortcut:

.. code-block:: bash

    pip install "ipython[qtconsole]"

or manual

.. code-block:: bash

    pip install pyzmq pygments

PyQt/PySide are not pip installable, so generally must be installed via system package managers (or conda).

.. _installnotebook:

Dependencies for the IPython HTML notebook
==========================================

The HTML notebook is a complex web application with quite a few dependencies:

pyzmq_, jinja2_, tornado_, mistune_, jsonschema_, pygments_, terminado_

Shortcut:

.. code-block:: bash

    pip install "ipython[notebook]"

or manual:

.. code-block:: bash

    pip install pyzmq jinja2 tornado mistune jsonschema pygments terminado

The IPython notebook is a notebook-style web interface to IPython and can be
started with the command ``ipython notebook``.

MathJax
-------

The IPython notebook uses the MathJax_ Javascript library for rendering LaTeX
in web browsers. Because MathJax is large, we don't include it with
IPython. Normally IPython will load MathJax from a CDN, but if you have a slow
network connection, or want to use LaTeX without an internet connection at all,
you can install MathJax locally.

A quick and easy method is to install it from a python session::

    python -m IPython.external.mathjax

If you need tighter configuration control, you can download your own copy
of MathJax from http://www.mathjax.org/download/ - use the MathJax-2.0 link.
When you have the file stored locally, install it with::

    python -m IPython.external.mathjax /path/to/source/mathjax-MathJax-v2.0-20-g07669ac.zip

For unusual needs, IPython can tell you what directory it wants to find MathJax in::

    python -m IPython.external.mathjax -d /some/other/mathjax

By default MathJax will be installed in your ipython directory, but you
can install MathJax system-wide.  Please refer to the documentation
of :mod:`IPython.external.mathjax`

Browser Compatibility
---------------------

The IPython notebook is officially supported on the following browsers:

* Chrome ≥ 13
* Safari ≥ 5
* Firefox ≥ 6

The is mainly due to the notebook's usage of WebSockets and the flexible box model.

The following browsers are unsupported:

* Safari < 5
* Firefox < 6
* Chrome < 13
* Opera (any): CSS issues, but execution might work
* Internet Explorer < 10
* Internet Explorer ≥ 10 (same as Opera)

Using Safari with HTTPS and an untrusted certificate is known to not work (websockets will fail).


Dependencies for nbconvert (converting notebooks to various formats)
====================================================================

For converting markdown to formats other than HTML, nbconvert uses Pandoc_ (1.12.1 or later).

To install pandoc on Linux, you can generally use your package manager::

    sudo apt-get install pandoc

On other platforms, you can get pandoc from `their website <http://johnmacfarlane.net/pandoc/installing.html>`_.


.. _ZeroMQ: http://www.zeromq.org
.. _PyZMQ: https://github.com/zeromq/pyzmq
.. _paramiko: https://github.com/robey/paramiko
.. _pygments: http://pygments.org
.. _pexpect: http://pexpect.readthedocs.org/en/latest/
.. _Jinja: http://jinja.pocoo.org
.. _Sphinx: http://sphinx-doc.org
.. _pandoc: http://johnmacfarlane.net/pandoc
.. _Tornado: http://www.tornadoweb.org
.. _MathJax: http://www.mathjax.org
.. _PyQt: http://www.riverbankcomputing.com/software/pyqt/intro
.. _PySide: http://qt-project.org/wiki/PySide
.. _jinja2: http://jinja.pocoo.org/
.. _mistune: https://github.com/lepture/mistune
.. _jsonschema: https://github.com/Julian/jsonschema
.. _terminado: https://github.com/takluyver/terminado