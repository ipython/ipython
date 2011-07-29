"""The basic dict based notebook format."""

import pprint
import uuid

from IPython.utils.ipstruct import Struct


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
    output_javascript=None):
    """Create a new code cell with input and output"""
    output = NotebookNode()
    if output_type is not None:
        output.output_type = unicode(output_type)
    if output_text is not None:
        output.text = unicode(output_text)
    if output_png is not None:
        output.png = bytes(output_png)
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

    return output


def new_code_cell(input=None, prompt_number=None, outputs=None, language=u'python'):
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

    return cell

def new_text_cell(text=None):
    """Create a new text cell."""
    cell = NotebookNode()
    if text is not None:
        cell.text = unicode(text)
    cell.cell_type = u'text'
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


def new_notebook(name=None, id=None, worksheets=None):
    """Create a notebook by name, id and a list of worksheets."""
    nb = NotebookNode()
    nb.nbformat = 2
    if name is not None:
        nb.name = unicode(name)
    if id is None:
        nb.id = unicode(uuid.uuid4())
    else:
        nb.id = unicode(id)
    if worksheets is None:
        nb.worksheets = []
    else:
        nb.worksheets = list(worksheets)
    return nb

