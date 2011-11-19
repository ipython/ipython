.. _documenting-ipython:

=====================
 Documenting IPython
=====================

When contributing code to IPython, you should strive for clarity and
consistency, without falling prey to a style straitjacket.  Basically,
'document everything, try to be consistent, do what makes sense.'

By and large we follow existing Python practices in major projects like Python
itself or NumPy, this document provides some additional detail for IPython.


Standalone documentation
========================

All standalone documentation should be written in plain text (``.txt``) files
using reStructuredText [reStructuredText]_ for markup and formatting. All such
documentation should be placed in the directory :file:`docs/source` of the
IPython source tree. Or, when appropriate, a suitably named subdirectory
should be used. The documentation in this location will serve as the main
source for IPython documentation.

The actual HTML and PDF docs are built using the Sphinx [Sphinx]_
documentation generation tool. Once you have Sphinx installed, you can build
the html docs yourself by doing:

.. code-block:: bash

    $ cd ipython-mybranch/docs
    $ make html

Our usage of Sphinx follows that of matplotlib [Matplotlib]_ closely. We are
using a number of Sphinx tools and extensions written by the matplotlib team
and will mostly follow their conventions, which are nicely spelled out in
their documentation guide [MatplotlibDocGuide]_. What follows is thus a
abridged version of the matplotlib documentation guide, taken with permission
from the matplotlib team.

If you are reading this in a web browser, you can click on the "Show Source"
link to see the original reStricturedText for the following examples.

A bit of Python code::

    for i in range(10):
        print i,
    print "A big number:",2**34

An interactive Python session::

    >>> from IPython.utils.path import get_ipython_dir
    >>> get_ipython_dir()
    '/home/fperez/.config/ipython'

An IPython session:

.. code-block:: ipython

  In [7]: import IPython

  In [8]: print "This IPython is version:",IPython.__version__
  This IPython is version: 0.9.1

  In [9]: 2+4
  Out[9]: 6


A bit of shell code:

.. code-block:: bash

    cd /tmp
    echo "My home directory is: $HOME"
    ls

Docstring format
================

Good docstrings are very important.  Unfortunately, Python itself only provides
a rather loose standard for docstrings [PEP257]_, and there is no universally
accepted convention for all the different parts of a complete docstring.
However, the NumPy project has established a very reasonable standard, and has
developed some tools to support the smooth inclusion of such docstrings in
Sphinx-generated manuals.  Rather than inventing yet another pseudo-standard,
IPython will be henceforth documented using the NumPy conventions; we carry
copies of some of the NumPy support tools to remain self-contained, but share
back upstream with NumPy any improvements or fixes we may make to the tools.

The NumPy documentation guidelines [NumPyDocGuide]_ contain detailed
information on this standard, and for a quick overview, the NumPy example
docstring [NumPyExampleDocstring]_ is a useful read.


For user-facing APIs, we try to be fairly strict about following the above
standards (even though they mean more verbose and detailed docstrings).
Wherever you can reasonably expect people to do introspection with::

  In [1]: some_function?

the docstring should follow the NumPy style and be fairly detailed.

For purely internal methods that are only likely to be read by others extending
IPython itself we are a bit more relaxed, especially for small/short methods
and functions whose intent is reasonably obvious.  We still expect docstrings
to be written, but they can be simpler.  For very short functions with a
single-line docstring you can use something like::

    def add(a, b):
       """The sum of two numbers.
       """
       code

and for longer multiline strings::

    def add(a, b):
       """The sum of two numbers.

       Here is the rest of the docs.
       """
       code


Here are two additional PEPs of interest regarding documentation of code.
While both of these were rejected, the ideas therein form much of the basis of
docutils (the machinery to process reStructuredText):

* `Docstring Processing System Framework <http://www.python.org/peps/pep-0256.html>`_
* `Docutils Design Specification <http://www.python.org/peps/pep-0258.html>`_

.. note::

   In the past IPython used epydoc so currently many docstrings still use
   epydoc conventions.  We will update them as we go, but all new code should
   be documented using the NumPy standard.
   
Building and uploading
======================
The built docs are stored in a separate repository. Through some github magic,
they're automatically exposed as a website. It works like this:

* You will need to have sphinx and latex installed. In Ubuntu, install
  ``texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended``.
  Install the latest version of sphinx from PyPI (``pip install sphinx``).
* Ensure that the development version of IPython is the first in your system
  path. You can either use a virtualenv, or modify your PYTHONPATH.
* Switch into the docs directory, and run ``make gh-pages``. This will build
  your updated docs as html and pdf, then automatically check out the latest
  version of the docs repository, copy the built docs into it, and commit your
  changes.
* Open the built docs in a web browser, and check that they're as expected.
* (When building the docs for a new tagged release, you will have to add its link to
  index.rst, then run ``python build_index.py`` to update index.html. Commit the 
  change.)
* Upload the docs with ``git push``. This only works if you have write access to
  the docs repository.
* If you are building a version that is not the current dev branch, nor a tagged release,
  then you must run gh-pages.py directly with ``python gh-pages.py <version>``, and *not*
  with ``make gh-pages``.

.. [reStructuredText] reStructuredText.  http://docutils.sourceforge.net/rst.html
.. [Sphinx] Sphinx. http://sphinx.pocoo.org/
.. [MatplotlibDocGuide] http://matplotlib.sourceforge.net/devel/documenting_mpl.html
.. [PEP257] PEP 257.  http://www.python.org/peps/pep-0257.html
.. [NumPyDocGuide] NumPy documentation guide. https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt
.. [NumPyExampleDocstring] NumPy example docstring.  https://github.com/numpy/numpy/blob/master/doc/HOWTO_BUILD_DOCS.rst.txt

