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


See http://jimmyg.org/blog/2009/sphinx-pdf-generation-with-latex.html

Pandoc, to convert markdown into latex
::

  sudo apt-get install pandoc

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
