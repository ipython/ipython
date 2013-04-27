"""Base class for doing notebook-to-notebook transformations.

This implements a converter class that turns an IPython notebook into another
IPython notebook, mainly so that it can be subclassed to perform more useful
and sophisticated transformations.
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2011, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Stdlib imports
import json
import os
from shutil import rmtree

# Our own imports
from .base import Converter
from .utils import cell_to_lines


#-----------------------------------------------------------------------------
# Class declarations
#-----------------------------------------------------------------------------
class ConverterNotebook(Converter):
    """
    A converter that is essentially a null-op.
    This exists so it can be subclassed
    for custom handlers of .ipynb files
    that create new .ipynb files.

    What distinguishes this from JSONWriter is that
    subclasses can specify what to do with each type of cell.

    Writes out a notebook file.

    """
    extension = 'ipynb'

    def __init__(self, infile=None, outbase=None, **kw):
        Converter.__init__(self, infile=infile, **kw)
        self.outbase = outbase
        rmtree(self.files_dir)

    def convert(self):
        return unicode(json.dumps(json.loads(Converter.convert(self, ',')),
                                  indent=1, sort_keys=True))

    def optional_header(self):
        s = \
"""{
 "metadata": {
 "name": "%(name)s"
 },
 "nbformat": 3,
 "worksheets": [
 {
 "cells": [""" % {'name': os.path.basename(self.outbase)}
        return s.split('\n')

    def optional_footer(self):
        s = \
"""]
  }
 ]
}"""
        return s.split('\n')

    def render_heading(self, cell):
        return cell_to_lines(cell)

    def render_code(self, cell):
        return cell_to_lines(cell)

    def render_markdown(self, cell):
        return cell_to_lines(cell)

    def render_raw(self, cell):
        return cell_to_lines(cell)

    def render_pyout(self, output):
        return cell_to_lines(output)

    def render_pyerr(self, output):
        return cell_to_lines(output)

    def render_display_format_text(self, output):
        return [output.text]

    def render_display_format_html(self, output):
        return [output.html]

    def render_display_format_latex(self, output):
        return [output.latex]

    def render_display_format_json(self, output):
        return [output.json]

    def render_display_format_javascript(self, output):
        return [output.javascript]
