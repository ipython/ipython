================================================================
 nbconvert: conversion utilities for the IPython notebook format
================================================================

Overview
========

nbconvert provides command line utilities to convert to and from IPython
notebooks and standard formats.

-   ReST
-   Markdown
-   HTML
-   TeX (through Sphinx)
-   Python script

As these tools mature, these utilities will be merged into IPython.

Requirements
============

Jinja2
~~~~~~

Most of the converter should rely on Jinja2 templating language.


Markdown
~~~~~~~~
You will need the `python markdown module
<http://pypi.python.org/pypi/Markdown>`_ ::


    $ pip install markdown

Docutils
~~~~~~~~

nbconvert require the latest development version of docutils. This can be installed
via ::

    $ curl http://docutils.svn.sourceforge.net/viewvc/docutils/trunk/docutils/?view=tar > docutils.tgz
    $ pip install -U docutils.tgz

Sphinx-Latex
~~~~~~~~~~~~

We are trying to require as little as possible, but for now, compiling the generated Tex file require texlive-full.
::

  sudo apt-get install texlive-full


See http://jimmyg.org/blog/2009/sphinx-pdf-generation-with-latex.html


Testing for Sphinx Latex
~~~~~~~~~~~~~~~~~~~~~~~~

To test, I place a Test1.ipynb file in my nbconvert directory.
Then I run this shell script

::

  mkdir Test1_files
  rm Test1_files/*

  python nbconvert2.py latex_sphinx_howto Test1.ipynb
  mv Test1.tex Test1_files/Test1.tex
  cd Test1_files
  pdflatex Test1.tex

This script will build a Sphinx-howto out of the Test1 IPython notebook.
Replace "howto" with "manual" to build a manual.

Tested against
https://github.com/unpingco/Python-for-Signal-Processing

Pandoc
~~~~~~

Nbconvert also needs the `pandoc multiformat converter
<http://johnmacfarlane.net/pandoc>`_ to do the actual text conversions.  Pandoc
is included in most linux distributions package managers, and the author's
website contains links to Mac OS X and Windows installers.

Pandoc, to convert markdown into latex
::

  sudo apt-get install pandoc

Pygment
~~~~~~~
For conversion to HTML/LaTeX, pygments is also required for syntax highlighting
::

    $ pip install pygments



Running Tests
=============

Please try to run the tests to avoid regression when commiting a patch, and create new test when adding features.
::

    $ pip install nose
    $ nosetests


Using nbconvert
===============

You will need to either put the source repository in your ``$PATH`` or symlink
the ``nbconvert.py`` script, as well as the ``css`` and ``js`` subdirectories
to a directory in your ``$PATH``.  Once this is done, you can call it as::

    $ nbconvert -f <FORMAT> notebook.ipynb

Use ``nbconvert -h`` for up to date help on the available formats.



