================================================================
 nbconvert: conversion utilities for the IPython notebook format
================================================================

Overview
========

nbconvert provides command line utilities to convert to and from IPython
notebooks and standard formats:

-   ReST
-   Markdown
-   HTML
-   Python script
-   Latex

As these tools mature, these utilities will be merged into IPython.

Requirements
============

You will need the `python markdown module
<http://pypi.python.org/pypi/Markdown>`_ ::

    $ pip install markdown
    
as well as the latest development version of docutils. This can be installed
via ::

    $ curl http://docutils.svn.sourceforge.net/viewvc/docutils/trunk/docutils/?view=tar > docutils.tgz
    $ pip install -U docutils.tgz

Nbconvert also needs the `pandoc multiformat converter
<http://johnmacfarlane.net/pandoc>`_ to do the actual text conversions.  Pandoc
is included in most linux distributions package managers, and the author's
website contains links to Mac OS X and Windows installers.
    
For conversion to HTML, pygments is also required
::

    $ pip install pygments


    
Running Tests
=============
::

    $ pip install nose
    $ nosetests


Using nbconvert
===============

You will need to either put the source repository in your ``$PATH`` or symlink
the ``nbconvert.py`` script, as well as the ``css`` and ``js`` subdirectories
to a directory in your ``$PATH``.  Once this is done, you can call it as::

  nbconvert -f <FORMAT> notebook.ipynb

Use ``nbconvert -h`` for up to date help on the available formats.
