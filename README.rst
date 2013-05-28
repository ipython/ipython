================================================================
 NbConvert: Conversion utilities for the IPython notebook format
================================================================



Overview
========

NbConvert provides a command line interface to convert to and from IPython
notebooks and standard formats.

 - ReST
 - Markdown
 - HTML
 - Python script
 - Reveal
 - LaTeX
 - Sphinx

As these functions mature, they will be merged into IPython.



Requirements
============

Jinja2
~~~~~~
All of the exporters rely on the Jinja2 templating language.


Markdown
~~~~~~~~
You will need the `python markdown module
<http://pypi.python.org/pypi/Markdown>`_ ::


    $ pip install markdown


Docutils
~~~~~~~~
nbconvert requires the latest development version of docutils. This can be installed
via ::

    $ curl http://docutils.svn.sourceforge.net/viewvc/docutils/trunk/docutils/?view=tar > docutils.tgz
    $ pip install -U docutils.tgz


Sphinx-Latex
~~~~~~~~~~~~
We are trying to require as little as possible, but for now, compiling the generated Tex file requires texlive-full.
::

  sudo apt-get install texlive-full


*See http://jimmyg.org/blog/2009/sphinx-pdf-generation-with-latex.html for more information*


Pandoc
~~~~~~
Nbconvert also needs the `pandoc multiformat converter
<http://johnmacfarlane.net/pandoc>`_ to do the actual text conversions.  Pandoc
is included in most Linux distribution's package managers, and the author's
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

Please try to run the tests to avoid regression when committing a patch, and create new tests when adding features.
::

    $ pip install nose
    $ nosetests



Using nbconvert
===============

You will need to either put the source repository in your ``$PATH`` or symlink
the ``nbconvert.py`` script to a directory in your ``$PATH``, e.g.::

    $ ln -s /usr/local/bin/nbconvert "$PWD/nbconvert.py"

Once this is done, you can call it as::

    $ nbconvert <FORMAT> notebook.ipynb

Use ``nbconvert -h`` for up to date help on the available formats.

