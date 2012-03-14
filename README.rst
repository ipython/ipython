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
-   PDF
-   Python script

As these tools mature, these utilities will be merged into IPython

Requirements
============
The latest development version of doctest is required. This can be installed via
::

    $ curl http://docutils.svn.sourceforge.net/viewvc/docutils/trunk/docutils/?view=tar > docutils.gz
    $ pip install -U docutils.gz

For conversion to HTML, pygments is also required
::

    $ pip install pygments

Running Tests
=============
::

    $ pip install nose
    $ nosetests
