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
from IPython.utils.py3compat import unicode_type

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

# Change this when incrementing the nbformat version
nbformat = 3
nbformat_minor = 0

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
    ename=None, evalue=None, traceback=None, stream=None, metadata=None):
    """Create a new code cell with input and output"""
    output = NotebookNode()
    if output_type is not None:
        output.output_type = unicode_type(output_type)

    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise TypeError("metadata must be dict")
    output.metadata = metadata

    if output_type != 'pyerr':
        if output_text is not None:
            output.text = unicode_type(output_text)
        if output_png is not None:
            output.png = bytes(output_png)
        if output_jpeg is not None:
            output.jpeg = bytes(output_jpeg)
        if output_html is not None:
            output.html = unicode_type(output_html)
        if output_svg is not None:
            output.svg = unicode_type(output_svg)
        if output_latex is not None:
            output.latex = unicode_type(output_latex)
        if output_json is not None:
            output.json = unicode_type(output_json)
        if output_javascript is not None:
            output.javascript = unicode_type(output_javascript)

    if output_type == u'pyout':
        if prompt_number is not None:
            output.prompt_number = int(prompt_number)

    if output_type == u'pyerr':
        if ename is not None:
            output.ename = unicode_type(ename)
        if evalue is not None:
            output.evalue = unicode_type(evalue)
        if traceback is not None:
            output.traceback = [unicode_type(frame) for frame in list(traceback)]

    if output_type == u'stream':
        output.stream = 'stdout' if stream is None else unicode_type(stream)
    
    return output


def new_code_cell(input=None, prompt_number=None, outputs=None,
    language=u'python', collapsed=False, metadata=None):
    """Create a new code cell with input and output"""
    cell = NotebookNode()
    cell.cell_type = u'code'
    if language is not None:
        cell.language = unicode_type(language)
    if input is not None:
        cell.input = unicode_type(input)
    if prompt_number is not None:
        cell.prompt_number = int(prompt_number)
    if outputs is None:
        cell.outputs = []
    else:
        cell.outputs = outputs
    if collapsed is not None:
        cell.collapsed = bool(collapsed)
    cell.metadata = NotebookNode(metadata or {})

    return cell

def new_text_cell(cell_type, source=None, rendered=None, metadata=None):
    """Create a new text cell."""
    cell = NotebookNode()
    # VERSIONHACK: plaintext -> raw
    # handle never-released plaintext name for raw cells
    if cell_type == 'plaintext':
        cell_type = 'raw'
    if source is not None:
        cell.source = unicode_type(source)
    if rendered is not None:
        cell.rendered = unicode_type(rendered)
    cell.metadata = NotebookNode(metadata or {})
    cell.cell_type = cell_type
    return cell


def new_heading_cell(source=None, rendered=None, level=1, metadata=None):
    """Create a new section cell with a given integer level."""
    cell = NotebookNode()
    cell.cell_type = u'heading'
    if source is not None:
        cell.source = unicode_type(source)
    if rendered is not None:
        cell.rendered = unicode_type(rendered)
    cell.level = int(level)
    cell.metadata = NotebookNode(metadata or {})
    return cell


def new_worksheet(name=None, cells=None, metadata=None):
    """Create a worksheet by name with with a list of cells."""
    ws = NotebookNode()
    if name is not None:
        ws.name = unicode_type(name)
    if cells is None:
        ws.cells = []
    else:
        ws.cells = list(cells)
    ws.metadata = NotebookNode(metadata or {})
    return ws


def new_notebook(name=None, metadata=None, worksheets=None):
    """Create a notebook by name, id and a list of worksheets."""
    nb = NotebookNode()
    nb.nbformat = nbformat
    nb.nbformat_minor = nbformat_minor
    if worksheets is None:
        nb.worksheets = []
    else:
        nb.worksheets = list(worksheets)
    if metadata is None:
        nb.metadata = new_metadata()
    else:
        nb.metadata = NotebookNode(metadata)
    if name is not None:
        nb.metadata.name = unicode_type(name)
    return nb


def new_metadata(name=None, authors=None, license=None, created=None,
    modified=None, gistid=None):
    """Create a new metadata node."""
    metadata = NotebookNode()
    if name is not None:
        metadata.name = unicode_type(name)
    if authors is not None:
        metadata.authors = list(authors)
    if created is not None:
        metadata.created = unicode_type(created)
    if modified is not None:
        metadata.modified = unicode_type(modified)
    if license is not None:
        metadata.license = unicode_type(license)
    if gistid is not None:
        metadata.gistid = unicode_type(gistid)
    return metadata

def new_author(name=None, email=None, affiliation=None, url=None):
    """Create a new author."""
    author = NotebookNode()
    if name is not None:
        author.name = unicode_type(name)
    if email is not None:
        author.email = unicode_type(email)
    if affiliation is not None:
        author.affiliation = unicode_type(affiliation)
    if url is not None:
        author.url = unicode_type(url)
    return author

