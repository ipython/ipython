"""Python API for composing notebook elements

The Python representation of a notebook is a nested structure of
dictionary subclasses that support attribute access
(IPython.utils.ipstruct.Struct). The functions in this module are merely
helpers to build the structs in the right form.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from IPython.utils.ipstruct import Struct

# Change this when incrementing the nbformat version
nbformat = 4
nbformat_minor = 0
nbformat_schema = 'nbformat.v4.schema.json'

def validate(node, ref=None):
    """validate a v4 node"""
    from ..current import validate
    return validate(node, ref=ref, version=nbformat)

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


def new_output(output_type, mime_bundle=None, **kwargs):
    """Create a new output, to go in the ``cell.outputs`` list of a code cell."""
    output = NotebookNode(output_type=output_type, **kwargs)
    if mime_bundle:
        output.update(mime_bundle)
    # populate defaults:
    output.setdefault('metadata', NotebookNode())
    if output_type == 'stream':
        output.setdefault('name', 'stdout')
        output.setdefault('text', '')
    validate(output, output_type)
    return output

def new_code_cell(source='', **kwargs):
    """Create a new code cell"""
    cell = NotebookNode(cell_type='code', source=source, **kwargs)
    cell.setdefault('metadata', NotebookNode())
    cell.setdefault('source', '')
    cell.setdefault('prompt_number', None)
    cell.setdefault('outputs', [])

    validate(cell, 'code_cell')
    return cell

def new_markdown_cell(source='', **kwargs):
    """Create a new markdown cell"""
    cell = NotebookNode(cell_type='markdown', source=source, **kwargs)
    cell.setdefault('metadata', NotebookNode())

    validate(cell, 'markdown_cell')
    return cell

def new_heading_cell(source='', **kwargs):
    """Create a new heading cell"""
    cell = NotebookNode(cell_type='heading', source=source, **kwargs)
    cell.setdefault('metadata', NotebookNode())
    cell.setdefault('level', 1)

    validate(cell, 'heading_cell')
    return cell

def new_raw_cell(source='', **kwargs):
    """Create a new raw cell"""
    cell = NotebookNode(cell_type='raw', source=source, **kwargs)
    cell.setdefault('metadata', NotebookNode())

    validate(cell, 'raw_cell')
    return cell

def new_notebook(**kwargs):
    """Create a new notebook"""
    nb = NotebookNode(**kwargs)
    nb.nbformat = nbformat
    nb.nbformat_minor = nbformat_minor
    nb.setdefault('cells', [])
    nb.setdefault('metadata', NotebookNode())
    validate(nb)
    return nb
