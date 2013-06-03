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


Quick Start
===========

Dependencies
~~~~~~~~~~~~

To install the necessary dependencies on a **Linux** machine:

::

    pip install jinja2 
    pip install markdown 
    curl http://docutils.svn.sourceforge.net/viewvc/docutils/trunk/docutils/?view=tar > docutils.tgz 
    pip install -U docutils.tgz 
    pip install pygments 
    sudo easy_install -U sphinx 
    sudo apt-get install texlive-full 
    sudo apt-get install pandoc

If you're on a **Mac**, the last two commands are executed in a different manner (since apt-get doesn't exist.)

::

    Install PanDoc via the installer http://code.google.com/p/pandoc/downloads/list
    Install MacTex via the .pkg http://www.tug.org/mactex/

Exporting
~~~~~~~~~

Now, to export a notebook you can call


::

    python nbconvert.py sphinx_howto book.ipynb --NbConvertApp.write=True --NbConvertApp.stdout=False

Where **book.ipynb** *is the name of the notebook* you'd like to convert
and **sphinx_howto** *is the output template name*.  See */nbconvert/templates/* and 
*/nbconvert/templates/sphinx/* for more.  NOTE: the template
extension should **not** be included in the template name.


This will create a file.ext (converted file) and /book_files/ directory with all of the output figures.  

Latex Only
~~~~~~~~~~

If you want to compile a PDF from LaTeX output, move the file.tex (conversion results) 
into the directory with all the figures /book_files/.  The  You can then run

::

    cd book_files       
    PdfLatex file.tex
   

Running Tests
=============

Please try to run the tests to avoid regression when committing a patch, and create new tests when adding features.
::

    $ pip install nose
    $ nosetests

