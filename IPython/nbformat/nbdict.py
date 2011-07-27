"""The basic dict based notebook format."""

import uuid


def new_code_cell(input=None, prompt_number=None, output_text=None, output_png=None,
    output_html=None, output_svg=None, output_latex=None, output_json=None, 
    output_javascript=None):
    """Create a new code cell with input and output"""
    cell = {}
    cell['cell_type'] = 'code'
    if input is not None:
        cell['input'] = unicode(input)
    if prompt_number is not None:
        cell['prompt_number'] = int(prompt_number)

    output = {}
    if output_text is not None:
        output['text/plain'] = unicode(output_text)
    if output_png is not None:
        output['image/png'] = bytes(output_png)
    if output_html is not None:
        output['text/html'] = unicode(output_html)
    if output_svg is not None:
        output['image/svg+xml'] = unicode(output_svg)
    if output_latex is not None:
        output['text/latex'] = unicode(output_latex)
    if output_json is not None:
        output['application/json'] = unicode(output_json)
    if output_javascript is not None:
        output['application/javascript'] = unicode(output_javascript)

    cell['output'] = output
    return cell


def new_text_cell(text=None):
    """Create a new text cell."""
    cell = {}
    if text is not None:
        cell['text'] = unicode(text)
    cell['cell_type'] = 'text'
    return cell


def new_worksheet(name=None, cells=None):
    """Create a worksheet by name with with a list of cells."""
    ws = {}
    if name is not None:
        ws['name'] = unicode(name)
    else:
        ws['name'] = u''
    if cells is None:
        ws['cells'] = []
    else:
        ws['cells'] = list(cells)
    return ws


def new_notebook(name=None, id=None, worksheets=None):
    """Create a notebook by name, id and a list of worksheets."""
    nb = {}
    if name is not None:
        nb['name'] = unicode(name)
    else:
        nb['name'] = u''
    if id is None:
        nb['id'] = unicode(uuid.uuid4())
    else:
        nb['id'] = unicode(id)
    if worksheets is None:
        nb['worksheets'] = []
    else:
        nb['worksheets'] = list(worksheets)
    return nb

