================================================================
 nbconvert Sphinx-Latex Jinja2 templates
================================================================

Overview
========

nbconvert provides command line utilities to convert to and from IPython
notebooks and standard formats.  However, the latex formatting leaves
something to be desired.  This repository contains a port of the beautiful
and popular Sphinx latex styles for nbconvert.

Requirements
============

Sphinx-Latex:

    $ sudo apt-get install texlive-full

See http://jimmyg.org/blog/2009/sphinx-pdf-generation-with-latex.html

*IMPORTANT:*

Markdown2latex is required, but this command will *NOT* work
    $ sudo Pip Install Markdown2latex
     
Instead
    $ sudo git clone https://github.com/bwkeller/markdown2latex.git
    $ cd markdown2latex
    $ sudo python setup.py build
    $ sudo python setup.py install
