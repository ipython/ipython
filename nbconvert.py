#!/usr/bin/env python
"""Convert IPython notebooks to other formats, such as ReST, and HTML.

Example:
  ./nbconvert.py --format rst file.ipynb

Produces 'file.rst', along with auto-generated figure files
called nb_figure_NN.png.
"""
#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Stdlib
import codecs
import io
import logging
import os
import pprint
import re
import subprocess
import sys
import json
import copy
from types import FunctionType
from shutil import rmtree
from markdown import markdown

# From IPython
from IPython.external import argparse
from IPython.nbformat import current as nbformat
from IPython.utils.text import indent
from IPython.nbformat.v3.nbjson import BytesEncoder
from IPython.utils import path, py3compat

# local
from lexers import IPythonLexer

from converters.html import ConverterHTML
from converters.markdown import ConverterMarkdown
from converters.bloggerhtml import ConverterBloggerHTML
from converters.rst import ConverterRST
from converters.latex import ConverterLaTeX

known_formats = "rst (default), html, blogger-html, latex, markdown, py"

def main(infile, format='rst'):
    """Convert a notebook to html in one step"""
    # XXX: this is just quick and dirty for now. When adding a new format,
    # make sure to add it to the `known_formats` string above, which gets
    # printed in in the catch-all else, as well as in the help
    if format == 'rst':
        converter = ConverterRST(infile)
        converter.render()
    elif format == 'markdown':
        converter = ConverterMarkdown(infile)
        converter.render()
    elif format == 'html':
        converter = ConverterHTML(infile)
        htmlfname = converter.render()
    elif format == 'blogger-html':
        converter = ConverterBloggerHTML(infile)
        htmlfname = converter.render()
    elif format == 'latex':
        converter = ConverterLaTeX(infile)
        latexfname = converter.render()
    elif format == 'py':
        converter = ConverterPy(infile)
        converter.render()
    else:
        raise SystemExit("Unknown format '%s', " % format +
                "known formats are: " + known_formats)

#-----------------------------------------------------------------------------
# Script main
#-----------------------------------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
            formatter_class=argparse.RawTextHelpFormatter)
    # TODO: consider passing file like object around, rather than filenames
    # would allow us to process stdin, or even http streams
    #parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)

    #Require a filename as a positional argument
    parser.add_argument('infile', nargs=1)
    parser.add_argument('-f', '--format', default='rst',
                        help='Output format. Supported formats: \n' +
                        known_formats)
    args = parser.parse_args()
    main(infile=args.infile[0], format=args.format)
