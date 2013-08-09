IPython requires Python 2.6, 2.7, or ≥ 3.2.

.. note::

    If you need to use Python 2.5, you can find an old version (≤0.10) of IPython
    `here <http://archive.ipython.org/release/>`__.

Quickstart
==========

If you have :mod:`setuptools`,
the quickest way to get up and running with IPython is:

.. code-block:: bash

    $ easy_install ipython[all]

This will download and install IPython and its main optional dependencies:

- jinja2, needed for the notebook
- sphinx, needed for nbconvert
- pyzmq, needed for IPython's parallel computing features, qt console and
  notebook
- pygments, used by nbconvert and the Qt console for syntax highlighting
- tornado, needed by the web-based notebook
- nose, used by the test suite
- readline (on OS X) or pyreadline (on Windows), needed for the terminal

To run IPython's test suite, use the :command:`iptest` command:

.. code-block:: bash

    $ iptest

.. note::

    .. code-block:: bash

        $ pip install ipython[all]
    
    will also work in many cases, but it will ignore the binary eggs
    of packages such as pyzmq and readline,
    which may be required for some users on Windows or OS X.


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

IPython and most dependencies can be installed via :command:`easy_install`,
provided by the :mod:`setuptools` package, or :command:`pip`.
In many scenarios, this is the most simplest method of installing Python packages.
More information about :mod:`setuptools` can be found on
`its PyPI page <http://pypi.python.org/pypi/setuptools>`__.

.. note::

   On Windows, IPython *requires* :mod:`setuptools`.  We hope to
   change this in the future, but for now on Windows, you *must* install
   :mod:`setuptools` to use IPython.

More general information about installing Python packages can be found in
`Python's documentation <http://docs.python.org>`_.


Installing IPython itself
=========================

Given a properly built Python, the basic interactive IPython shell will work
with no external dependencies.  However, some Python distributions
(particularly on Windows and OS X), don't come with a working :mod:`readline`
module.  The IPython shell will work without :mod:`readline`, but will lack
many features that users depend on, such as tab completion and command line
editing.  If you install IPython with :mod:`setuptools`, (e.g. with
`easy_install`), then the appropriate :mod:`readline` for your platform will be
installed.  See below for details of how to make sure you have a working
:mod:`readline`.

Installation using easy_install or pip
--------------------------------------

If you have :mod:`setuptools` or :mod:`pip`, the easiest way of getting IPython is
to simply use :command:`easy_install` or :command:`pip`:

.. code-block:: bash

    $ pip install ipython

That's it.

.. note::

    Many prefer :command:`pip` to :command:`easy_install`, but it ignores eggs (binary Python packages).
    This mainly affects pyzmq and readline, which are compiled packages and provide
    binary eggs.  If you use :command:`pip` to install these packages,
    it will always compile from source, which may not succeed.

Installation from source
------------------------

If you don't want to use :command:`easy_install`, or don't have it installed,
just grab the latest stable build of IPython from `here
<http://ipython.org/download.html>`_.  Then do the following:

.. code-block:: bash

    $ tar -xzf ipython.tar.gz
    $ cd ipython
    $ python setup.py install

If you are installing to a location (like ``/usr/local``) that requires higher
permissions, you may need to run the last command with :command:`sudo`.

Windows
-------

As mentioned above, on Windows, IPython requires :mod:`setuptools`, and it also
requires the PyReadline library to properly support coloring and keyboard
management (features that the default windows console doesn't have).  So on
Windows, the installation procedure is:

1. Install `setuptools <http://pypi.python.org/pypi/setuptools>`_.

2. Install `pyreadline <http://pypi.python.org/pypi/pyreadline>`_.  You can use
   the command ``easy_install pyreadline`` from a terminal, or the binary
   installer appropriate for your platform from the PyPI page.

3. Install IPython itself, which you can download from `PyPI
   <http://pypi.python.org/pypi/ipython>`_ or from `our site
   <http://ipython.org/download.html>`_.  Note that on Windows 7, you *must*
   right-click and 'Run as administrator' for the Start menu shortcuts to be
   created.

IPython by default runs in a terminal window, but the normal terminal
application supplied by Microsoft Windows is very primitive.  You may want to
download the excellent and free Console_ application instead, which is a far
superior tool.  You can even configure Console to give you by default an
IPython tab, which is very convenient to create new IPython sessions directly
from the working terminal.

.. _Console:  http://sourceforge.net/projects/console

   
Installing the development version
----------------------------------

It is also possible to install the development version of IPython from our
`Git <http://git-scm.com/>`_ source code repository.  To do this you will
need to have Git installed on your system.  Then just do:

.. code-block:: bash

    $ git clone --recursive https://github.com/ipython/ipython.git
    $ cd ipython
    $ python setup.py install

Some users want to be able to follow the development branch as it changes.  If
you have :mod:`setuptools` installed, this is easy. Simply replace the last
step by:

.. code-block:: bash

    $ python setupegg.py develop

This creates links in the right places and installs the command line script to
the appropriate places.  Then, if you want to update your IPython at any time,
just do:

.. code-block:: bash

    $ git pull


Basic optional dependencies
===========================

There are a number of basic optional dependencies that most users will want to
get.  These are:

* readline (for command line editing, tab completion, etc.)
* nose (to run the IPython test suite)
* pexpect (to use things like irunner)

If you are comfortable installing these things yourself, have at it, otherwise
read on for more details.

readline
--------

As indicated above, on Windows, PyReadline is a *mandatory* dependency.
PyReadline is a separate, Windows only implementation of readline that uses
native Windows calls through :mod:`ctypes`. The easiest way of installing
PyReadline is you use the binary installer available `here
<http://pypi.python.org/pypi/pyreadline>`__.

On OSX, if you are using the built-in Python shipped by Apple, you will be
missing a full readline implementation as Apple ships instead a library called
``libedit`` that provides only some of readline's functionality.  While you may
find libedit sufficient, we have occasional reports of bugs with it and several
developers who use OS X as their main environment consider libedit unacceptable
for productive, regular use with IPython.

Therefore, we *strongly* recommend that on OS X you get the full
:mod:`readline` module.  We will *not* consider completion/history problems to
be bugs for IPython if you are using libedit.

To get a working :mod:`readline` module, just do (with :mod:`setuptools`
installed):

.. code-block:: bash

    $ easy_install readline

.. note::

    Other Python distributions on OS X (such as fink, MacPorts and the official
    python.org binaries) already have readline installed so you likely don't
    have to do this step.

When IPython is installed with :mod:`setuptools`, (e.g. using the
``easy_install`` command), readline is added as a dependency on OS X, and
PyReadline on Windows, and will be installed on your system.  However, if you
do not use setuptools, you may have to install one of these packages yourself.


nose
----

To run the IPython test suite you will need the :mod:`nose` package.  Nose
provides a great way of sniffing out and running all of the IPython tests.  The
simplest way of getting nose is to use :command:`easy_install` or :command:`pip`:

.. code-block:: bash

    $ pip install nose

Another way of getting this is to do:

.. code-block:: bash

    $ pip install ipython[test]

For more installation options, see the `nose website
<http://somethingaboutorange.com/mrl/projects/nose/>`_.  

Once you have nose installed, you can run IPython's test suite using the
iptest command:

.. code-block:: bash

    $ iptest

pexpect
-------

The pexpect_ package is used in IPython's :command:`irunner` script, as well as
for managing subprocesses. IPython now includes a version of pexpect in
:mod:`IPython.external`, but if you have installed pexpect, IPython will use
that instead. On Unix platforms (including OS X), just do:

.. code-block:: bash

    $ pip install pexpect
    
.. note::

    On Python 3, you should actually install :mod:`pexpect-u`,
    a unicode-safe fork of pexpect.

Windows users are out of luck as pexpect does not run there.

Dependencies for IPython.parallel (parallel computing)
======================================================

IPython.parallel provides a nice architecture for parallel computing, with a
focus on fluid interactive workflows.  These features require just one package:
PyZMQ.  See the next section for PyZMQ details.

On a Unix style platform (including OS X), if you want to use
:mod:`setuptools`, you can just do:

.. code-block:: bash

    $ easy_install ipython[zmq]    # will include pyzmq

Security in IPython.parallel is provided by SSH tunnels.  By default, Linux
and OSX clients will use the shell ssh command, but on Windows, we also
support tunneling with paramiko_.

Dependencies for IPython.kernel.zmq
===================================

pyzmq
-----

IPython 0.11 introduced some new functionality, including a two-process
execution model using ZeroMQ_ for communication. The Python bindings to ZeroMQ
are found in the PyZMQ_ project, which is easy_install-able once you have
ZeroMQ installed.  If you are on Python 2.6 or 2.7 on OSX, or 2.7 on Windows,
pyzmq has eggs that include ZeroMQ itself.

IPython.kernel.zmq depends on pyzmq >= 2.1.4.

Dependencies for the IPython QT console
=======================================

pyzmq
-----

Like the :mod:`IPython.parallel` package, the QT Console requires ZeroMQ and
PyZMQ.

Qt
--

Also with 0.11, a new GUI was added using the work in :mod:`IPython.kernel.zmq`, which
can be launched with ``ipython qtconsole``. The GUI is built on Qt, and works
with either PyQt, which can be installed from the `PyQt website
<http://www.riverbankcomputing.co.uk/>`_, or `PySide
<http://www.pyside.org/>`_, from Nokia.

pygments
--------

The syntax-highlighting in ``ipython qtconsole`` is done with the pygments_
project, which is easy_install-able.

.. _installnotebook:

Dependencies for the IPython HTML notebook
==========================================

The IPython notebook is a notebook-style web interface to IPython and can be
started with the command ``ipython notebook``.

pyzmq
-----

Like the :mod:`IPython.parallel` and :mod:`IPython.frontend.qt.console`
packages, the HTML notebook requires ZeroMQ and PyZMQ.

Tornado
-------

The IPython notebook uses the Tornado_ project for its HTTP server.  Tornado 2.1
is required, in order to support current versions of browsers, due to an update
to the websocket protocol.

Jinja
-----

The IPython notebook uses the Jinja_ templating tool to render HTML pages.


MathJax
-------

The IPython notebook uses the MathJax_ Javascript library for rendering LaTeX
in web browsers. Because MathJax is large, we don't include it with
IPython. Normally IPython will load MathJax from a CDN, but if you have a slow
network connection, or want to use LaTeX without an internet connection at all,
you can install MathJax locally.

A quick and easy method is to install it from a python session::

    from IPython.external.mathjax import install_mathjax
    install_mathjax()

If you need tighter configuration control, you can download your own copy
of MathJax from http://www.mathjax.org/download/ - use the MathJax-2.0 link.
When you have the file stored locally, install it with::

	python -m IPython.external.mathjax /path/to/source/mathjax-MathJax-v2.0-20-g07669ac.zip

For unusual needs, IPython can tell you what directory it wants to find MathJax in::

	python -m IPython.external.mathjax -d /some/other/mathjax

By default Mathjax will be installed in your ipython profile directory, but you
can make system wide install, please refer to the documentation and helper function 
of :mod:`IPython.external.mathjax`

Browser Compatibility
---------------------

The IPython notebook is officially supported on the following browers:

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

The following specific combinations are known **NOT** to work:

* Safari, IPython 0.12, tornado ≥ 2.2.0
* Safari with HTTPS connection to notebook and an untrusted certificate (websockets will fail)
* The [diigo Chrome extension](http://help.diigo.com/tools/chrome-extension) seems to interfere with scrolling

There are some early reports that the Notebook works on Internet Explorer 10, but we
expect there will be some CSS issues related to the flexible box model.


Dependencies for nbconvert (converting notebooks to various formats)
====================================================================

pandoc
------

The most important dependency of nbconvert is Pandoc_, a document format translation program.
This is not a Python package, so it cannot be expressed as a regular IPython dependency with setuptools.

To install pandoc on Linux, you can generally use your package manager::

    sudo apt-get install pandoc

On other platforms, you can get pandoc from `their website <http://johnmacfarlane.net/pandoc/installing.html>`_.


.. _ZeroMQ: http://www.zeromq.org
.. _PyZMQ: https://github.com/zeromq/pyzmq
.. _paramiko: https://github.com/robey/paramiko
.. _pygments: http://pygments.org
.. _pexpect: http://www.noah.org/wiki/Pexpect
.. _Jinja: http://jinja.pocoo.org
.. _Sphinx: http://sphinx-doc.org
.. _pandoc: http://johnmacfarlane.net/pandoc
.. _Tornado: http://www.tornadoweb.org
.. _MathJax: http://www.mathjax.org
