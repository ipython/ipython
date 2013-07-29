

.. _`nbconvert script`:

Converting notebooks to other formats
=====================================

Newly added in the 1.0 release of IPython is the ``nbconvert`` tool, which 
allows you to convert an ``.ipynb`` notebook document file into various static 
formats. 

Currently, ``nbconvert`` is provided as a command line tool, run as a script 
using IPython. In the future, a direct export capability from within the 
IPython Notebook web app is planned. 

The command-line syntax to run the ``nbconvert`` script is::

  $ ipython nbconvert --format=FORMAT notebook.ipynb

This will convert the IPython document file ``notebook.ipynb`` into the output 
format given by the ``FORMAT`` string.

The default output format is HTML, for which the ``--format`` modifier may be 
omitted::
  
  $ ipython nbconvert notebook.ipynb

The currently supported export formats are the following:

* HTML:

  - **full_html**:
    Standard HTML

  - **simple_html**:
    Simplified HTML

  - **reveal**:
    HTML slideshow presentation for use with the ``reveal.js`` package

* PDF:

  - **sphinx_howto**:
    The format for Sphinx_ HOWTOs; similar to an ``article`` in LaTeX

  - **sphinx_manual**:
    The format for Sphinx_ manuals; similar to a ``book`` in LaTeX 

  - **latex**:
    An article formatted completely using LaTeX

* Markup:

  - **rst**:
    reStructuredText_ markup

  - **markdown**:
    Markdown_ markup

.. _Sphinx: http://sphinx-doc.org/
.. _reStructuredText: http://docutils.sourceforge.net/rst.html
.. _Markdown: http://daringfireball.net/projects/markdown/syntax

* Python:

    Comments out all the non-Python code to produce a ``.py`` Python
    script with just the code content. Currently the output includes IPython 
    magics, and so can be run with ``ipython``, after changing the extension 
    of the script to ``.ipy``.
    
The files output file created by ``nbconvert`` will have the same base name as
the notebook and will be placed in the current working directory. Any
supporting files (graphics, etc) will be placed in a new directory with the
same base name as the notebook, suffixed with ``_files``::

  $ ipython nbconvert notebook.ipynb
  $ ls
  notebook.ipynb   notebook.html    notebook_files/

Each of the options for PDF export produces as an intermediate step a LaTeX 
``.tex`` file with the same basename as the notebook, as well as individual 
files for each figure, and ``.text`` files with textual output from running
code cells.

To actually produce the final PDF file, run the following commands::
  
  $ ipython nbconvert --format=latex notebook.ipynb
  $ pdflatex notebook

This requires a local installation of LaTeX on your machine.
The output is a PDF file ``notebook.pdf``, also placed inside the 
``nbconvert_build`` subdirectory.

Alternatively, the output may be sent to standard output with::
    
  $ ipython nbconvert notebook.ipynb --stdout
    
Multiple notebooks can be specified from the command line::
    
  $ ipython nbconvert notebook*.ipynb
  $ ipython nbconvert notebook1.ipynb notebook2.ipynb
    
or via a list in a configuration file, say ``mycfg.py``, containing the text::

  c = get_config()
  c.NbConvertApp.notebooks = ["notebook1.ipynb", "notebook2.ipynb"]

and using the command::

  $ ipython nbconvert --config mycfg.py


Extracting standard Python files from notebooks
-----------------------------------------------
``.ipynb`` notebook document files are plain text files which store a 
representation in JSON format of the contents of a notebook space. As such, 
they are not valid ``.py`` Python scripts, and so can be neither imported 
directly with ``import`` in Python, nor run directly as a standard Python 
script (though both of these are possible with simple workarounds).


To extract the Python code from within a notebook document, the simplest 
method is to use the ``File | Download as | Python (.py)`` menu item; the 
resulting ``.py`` script will be downloaded to your browser's  default 
download location.

An alternative is to pass an argument to the IPython Notebook, from the moment 
when it is originally started, specifying that whenever it saves an ``.ipynb`` 
notebook document, it should, at the same time, save the corresponding 
 ``.py`` script. To do so, you can execute the following command::

  $ ipython notebook --script

or you can set this option permanently in your configuration file with::

  c = get_config()
  c.NotebookManager.save_script=True

The result is that standard ``.py`` files are also now generated, which 
can be ``%run``, imported from regular IPython sessions or other notebooks, or 
executed at the command line, as usual.  Since the raw code you have typed is 
exported, you must avoid using syntax such as IPython magics and other 
IPython-specific extensions to the language for the files to be able to be 
successfully imported.
.. or you can change the script's extension to ``.ipy`` and run it with::
..
..  $ ipython script.ipy

In normal Python practice, the standard way to differentiate importable code 
in a Python script from the "executable" part of a script is to use the 
following idiom at the start of the executable part of the code::

  if __name__ == '__main__'

    # rest of the code...
  
Since all cells in the notebook are run as top-level code, you will need to
similarly protect *all* cells that you do not want executed when other scripts
try to import your notebook.  A convenient shortand for this is to define 
early on::

  script = __name__ == '__main__'

Then in any cell that you need to protect, use::

  if script:
    # rest of the cell...



.. _notebook_format:

Notebook JSON file format
-------------------------
Notebook documents are JSON files with an ``.ipynb`` extension, formatted
as legibly as possible with minimal extra indentation and cell content broken
across lines to make them reasonably friendly to use in version-control
workflows.  You should be very careful if you ever manually edit this JSON
data, as it is extremely easy to corrupt its internal structure and make the
file impossible to load.  In general, you should consider the notebook as a
file meant only to be edited by the IPython Notebook app itself, not for 
hand-editing.

.. note::

     Binary data such as figures are also saved directly in the JSON file.  
     This provides convenient single-file portability, but means that the 
     files can be large; a ``diff`` of binary data is also not very 
     meaningful.  Since the binary blobs are encoded in a single line, they 
     affect only one line of the ``diff`` output, but they are typically very 
     long lines.  You can use the ``Cell | All Output | Clear`` menu option to 
     remove all output from a notebook prior to committing it to version 
     control, if this is a concern.

The notebook server can also generate a pure Python version of your notebook, 
using the ``File | Download as`` menu option. The resulting ``.py`` file will 
contain all the code cells from your notebook verbatim, and all Markdown cells 
prepended with a comment marker.  The separation between code and Markdown
cells is indicated with special comments and there is a header indicating the
format version.  All output is removed when exporting to Python.

As an example, consider a simple notebook called ``simple.ipynb`` which 
contains one Markdown cell, with the content ``The simplest notebook.``, one 
code input cell with the content ``print "Hello, IPython!"``, and the 
corresponding output.

The contents of the notebook document ``simple.ipynb`` is the following JSON 
container::

  {
   "metadata": {
    "name": "simple"
   },
   "nbformat": 3,
   "nbformat_minor": 0,
   "worksheets": [
    {
     "cells": [
      {
       "cell_type": "markdown",
       "metadata": {},
       "source": "The simplest notebook."
      },
      {
       "cell_type": "code",
       "collapsed": false,
       "input": "print \"Hello, IPython\"",
       "language": "python",
       "metadata": {},
       "outputs": [
        {
         "output_type": "stream",
         "stream": "stdout",
         "text": "Hello, IPython\n"
        }
       ],
       "prompt_number": 1
      }
     ],
     "metadata": {}
    }
   ]
  }


The corresponding Python script is::

  # -*- coding: utf-8 -*-
  # <nbformat>3.0</nbformat>

  # <markdowncell>

  # The simplest notebook.

  # <codecell>

  print "Hello, IPython"

Note that indeed the output of the code cell, which is present in the JSON 
container, has been removed in the ``.py`` script.

