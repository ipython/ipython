.. image:: https://codecov.io/github/ipython/ipython/coverage.svg?branch=main
    :target: https://codecov.io/github/ipython/ipython?branch=main

.. image:: https://img.shields.io/pypi/v/IPython.svg
    :target: https://pypi.python.org/pypi/ipython

.. image:: https://github.com/ipython/ipython/actions/workflows/test.yml/badge.svg
    :target: https://github.com/ipython/ipython/actions/workflows/test.yml

.. image:: https://www.codetriage.com/ipython/ipython/badges/users.svg
    :target: https://www.codetriage.com/ipython/ipython/

.. image:: https://raster.shields.io/badge/Follows-SPEC--0000-brightgreen.png
    :target: https://scientific-python.org/specs/spec-0000/

.. image:: https://tidelift.com/badges/package/pypi/ipython?style=flat
    :target: https://tidelift.com/subscription/pkg/pypi-ipython


===========================================
 IPython: Productive Interactive Computing
===========================================

Overview
========

Welcome to IPython.  Our full documentation is available on `ipython.readthedocs.io
<https://ipython.readthedocs.io/en/stable/>`_ and contains information on how to install, use, and
contribute to the project.
IPython (Interactive Python) is a command shell for interactive computing in multiple programming languages, originally developed for the Python programming language, that offers introspection, rich media, shell syntax, tab completion, and history.

**IPython versions and Python Support**

Starting after IPython 8.16, we will progressively transition to `Spec-0000 <https://scientific-python.org/specs/spec-0000/>`_.

Starting with IPython 7.10, IPython follows `NEP 29 <https://numpy.org/neps/nep-0029-deprecation_policy.html>`_

**IPython 7.17+** requires Python version 3.7 and above.

**IPython 7.10+** requires Python version 3.6 and above.

**IPython 7.0** requires Python version 3.5 and above.

**IPython 6.x** requires Python version 3.3 and above.

**IPython 5.x LTS** is the compatible release for Python 2.7.
If you require Python 2 support, you **must** use IPython 5.x LTS. Please
update your project configurations and requirements as necessary.


The Notebook, Qt console and a number of other pieces are now parts of *Jupyter*.
See the `Jupyter installation docs <https://jupyter.readthedocs.io/en/latest/install.html>`__
if you want to use these.

Main features of IPython
========================
Comprehensive object introspection.

Input history, persistent across sessions.

Caching of output results during a session with automatically generated references.

Extensible tab completion, with support by default for completion of python variables and keywords, filenames and function keywords.

Extensible system of ‘magic’ commands for controlling the environment and performing many tasks related to IPython or the operating system.

A rich configuration system with easy switching between different setups (simpler than changing $PYTHONSTARTUP environment variables every time).

Session logging and reloading.

Extensible syntax processing for special purpose situations.

Access to the system shell with user-extensible alias system.

Easily embeddable in other Python programs and GUIs.

Integrated access to the pdb debugger and the Python profiler.


Development and Instant running
===============================

You can find the latest version of the development documentation on `readthedocs
<https://ipython.readthedocs.io/en/latest/>`_.

You can run IPython from this directory without even installing it system-wide
by typing at the terminal::

   $ python -m IPython

Or see the `development installation docs
<https://ipython.readthedocs.io/en/latest/install/install.html#installing-the-development-version>`_
for the latest revision on read the docs.

Documentation and installation instructions for older version of IPython can be
found on the `IPython website <https://ipython.org/documentation.html>`_


Alternatives to IPython
=======================

IPython may not be to your taste; if that's the case there might be similar
project that you might want to use:

- The classic Python REPL.
- `bpython <https://bpython-interpreter.org/>`_
- `mypython <https://www.asmeurer.com/mypython/>`_
- `ptpython and ptipython <https://pypi.org/project/ptpython/>`_
- `Xonsh <https://xon.sh/>`_

Ignoring commits with git blame.ignoreRevsFile
==============================================

As of git 2.23, it is possible to make formatting changes without breaking
``git blame``. See the `git documentation
<https://git-scm.com/docs/git-config#Documentation/git-config.txt-blameignoreRevsFile>`_
for more details.

To use this feature you must:

- Install git >= 2.23
- Configure your local git repo by running:
   - POSIX: ``tools\configure-git-blame-ignore-revs.sh``
   - Windows:  ``tools\configure-git-blame-ignore-revs.bat``
