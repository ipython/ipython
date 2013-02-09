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
::
    sudo apt-get install texlive-full
::

See http://jimmyg.org/blog/2009/sphinx-pdf-generation-with-latex.html

Pandoc, to convert markdown into latex
::
    sudo apt-get install pandoc
::

Testing
=======

To test, I place a Test1.ipynb file in my nbconvert directory.
Then I run this shell script:

::
mkdir test_out
rm test_out/*
cp Test1.ipynb test_out/Test1.ipynb
cp templates/tex/*.cls test_out/
cp templates/tex/*.sty test_out/

python nbconvert2.py latex_sphinx_manual test_out/Test1.ipynb
cd test_out
pdflatex Test1.tex
mv Test1.pdf Test1_Manual.pdf
cd ..

python nbconvert2.py latex_sphinx_howto test_out/Test1.ipynb
cd test_out
pdflatex Test1.tex
mv Test1.pdf Test1_HowTo.pdf
cd ..
::

This script will build both a Sphinx-howto and a Sphinx-manual out of the
Test1 IPython notebook.
