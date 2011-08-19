"""The basic dict based notebook format.

The Python representation of a notebook is a nested structure of 
dictionary subclasses that support attribute access
(IPython.utils.ipstruct.Struct). The functions in this module are merely
helpers to build the structs in the right form.

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import pprint
import uuid

from IPython.utils.ipstruct import Struct

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

class NotebookNode(Struct):
    pass


def from_dict(d):
    if isinstance(d, dict):
        newd = NotebookNode()
        for k,v in d.items():
            newd[k] = from_dict(v)
        return newd
    elif isinstance(d, (tuple, list)):
        return [from_dict(i) for i in d]
    else:
        return d


def new_output(output_type=None, output_text=None, output_png=None,
    output_html=None, output_svg=None, output_latex=None, output_json=None, 
    output_javascript=None, output_jpeg=None, prompt_number=None,
    etype=None, evalue=None, traceback=None):
    """Create a new code cell with input and output"""
    output = NotebookNode()
    if output_type is not None:
        output.output_type = unicode(output_type)

    if output_type != 'pyerr':
        if output_text is not None:
            output.text = unicode(output_text)
        if output_png is not None:
            output.png = bytes(output_png)
        if output_jpeg is not None:
            output.jpeg = bytes(output_jpeg)
        if output_html is not None:
            output.html = unicode(output_html)
        if output_svg is not None:
            output.svg = unicode(output_svg)
        if output_latex is not None:
            output.latex = unicode(output_latex)
        if output_json is not None:
            output.json = unicode(output_json)
        if output_javascript is not None:
            output.javascript = unicode(output_javascript)

    if output_type == u'pyout':
        if prompt_number is not None:
            output.prompt_number = int(prompt_number)

    if output_type == u'pyerr':
        if etype is not None:
            output.etype = unicode(etype)
        if evalue is not None:
            output.evalue = unicode(evalue)
        if traceback is not None:
            output.traceback = [unicode(frame) for frame in list(traceback)]

    return output


def new_code_cell(input=None, prompt_number=None, outputs=None,
    language=u'python', collapsed=False):
    """Create a new code cell with input and output"""
    cell = NotebookNode()
    cell.cell_type = u'code'
    if language is not None:
        cell.language = unicode(language)
    if input is not None:
        cell.input = unicode(input)
    if prompt_number is not None:
        cell.prompt_number = int(prompt_number)
    if outputs is None:
        cell.outputs = []
    else:
        cell.outputs = outputs
    if collapsed is not None:
        cell.collapsed = bool(collapsed)

    return cell

def new_text_cell(cell_type, source=None, rendered=None):
    """Create a new text cell."""
    cell = NotebookNode()
    if source is not None:
        cell.source = unicode(source)
    if rendered is not None:
        cell.rendered = unicode(rendered)
    cell.cell_type = cell_type
    return cell


def new_worksheet(name=None, cells=None):
    """Create a worksheet by name with with a list of cells."""
    ws = NotebookNode()
    if name is not None:
        ws.name = unicode(name)
    if cells is None:
        ws.cells = []
    else:
        ws.cells = list(cells)
    return ws


def new_notebook(name=None, worksheets=None, author=None, email=None,
    created=None, saved=None, license=None):
    """Create a notebook by name, id and a list of worksheets."""
    nb = NotebookNode()
    nb.nbformat = 2
    if name is not None:
        nb.name = unicode(name)
    if worksheets is None:
        nb.worksheets = []
    else:
        nb.worksheets = list(worksheets)
    if author is not None:
        nb.author = unicode(author)
    if email is not None:
        nb.email = unicode(email)
    if created is not None:
        nb.created = unicode(created)
    if saved is not None:
        nb.saved = unicode(saved)
    if license is not None:
        nb.license = unicode(license)
    return nb

