"""Code for converting notebooks to and from v3."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from .nbbase import (
    nbformat, nbformat_minor,
)

from IPython.nbformat import v3

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

def upgrade(nb, from_version=3, from_minor=0):
    """Convert a notebook to v4.

    Parameters
    ----------
    nb : NotebookNode
        The Python representation of the notebook to convert.
    from_version : int
        The original version of the notebook to convert.
    from_minor : int
        The original minor version of the notebook to convert (only relevant for v >= 3).
    """
    if from_version == 3:
        # Mark the original nbformat so consumers know it has been converted.
        nb.nbformat = nbformat
        nb.nbformat_minor = nbformat_minor

        nb.orig_nbformat = 3
        # remove worksheet(s)
        nb['cells'] = cells = []
        # In the unlikely event of multiple worksheets,
        # they will be flattened
        for ws in nb.pop('worksheets', []):
            # upgrade each cell
            for cell in ws['cells']:
                cells.append(upgrade_cell(cell))
        # upgrade metadata?
        nb.metadata.pop('name', '')
        return nb
    elif from_version == 4:
        # nothing to do
        if from_minor != nbformat_minor:
            nb.orig_nbformat_minor = from_minor
        nb.nbformat_minor = nbformat_minor
        return nb
    else:
        raise ValueError('Cannot convert a notebook directly from v%s to v4.  ' \
                'Try using the IPython.nbformat.convert module.' % from_version)

def upgrade_cell(cell):
    """upgrade a cell from v3 to v4

    code cell:
        - remove language metadata
        - cell.input -> cell.source
        - update outputs
    """
    if cell.cell_type == 'code':
        cell.metadata.pop('language', '')
        cell.source = cell.pop('input')
        cell.outputs = upgrade_outputs(cell)
    return cell

def downgrade_cell(cell):
    if cell.cell_type == 'code':
        cell.input = cell.pop('source')
        cell.outputs = downgrade_outputs(cell)
    return cell

_mime_map = {
    "text" : "text/plain",
    "html" : "text/html",
    "svg" : "image/svg+xml",
    "png" : "image/png",
    "jpeg" : "image/jpeg",
    "latex" : "text/latex",
    "json" : "application/json",
    "javascript" : "application/javascript",
};

def to_mime_key(d):
    """convert dict with v3 aliases to plain mime-type keys"""
    for alias, mime in _mime_map.items():
        if alias in d:
            d[mime] = d.pop(alias)
    return d

def from_mime_key(d):
    """convert dict with mime-type keys to v3 aliases"""
    for alias, mime in _mime_map.items():
        if mime in d:
            d[alias] = d.pop(mime)
    return d

def upgrade_output(output):
    """upgrade a single code cell output from v3 to v4

    - pyout -> execute_result
    - pyerr -> error
    - mime-type keys
    """
    if output['output_type'] == 'pyout':
        output['output_type'] = 'execute_result'
        to_mime_key(output)
        to_mime_key(output.get('metadata', {}))
    elif output['output_type'] == 'pyerr':
        output['output_type'] = 'error'
    elif output['output_type'] == 'display_data':
        to_mime_key(output)
        to_mime_key(output.get('metadata', {}))
    return output

def downgrade_output(output):
    """downgrade a single code cell output to v3 from v4

    - pyout <- execute_result
    - pyerr <- error
    - un-mime-type keys
    """
    if output['output_type'] == 'execute_result':
        output['output_type'] = 'pyout'
        from_mime_key(output)
        from_mime_key(output.get('metadata', {}))
    elif output['output_type'] == 'error':
        output['output_type'] = 'pyerr'
    elif output['output_type'] == 'display_data':
        from_mime_key(output)
        from_mime_key(output.get('metadata', {}))
    return output

def upgrade_outputs(outputs):
    """upgrade outputs of a code cell from v3 to v4"""
    return [upgrade_output(op) for op in outputs]

def downgrade_outputs(outputs):
    """downgrade outputs of a code cell to v3 from v4"""
    return [downgrade_output(op) for op in outputs]

def downgrade(nb):
    """Convert a v4 notebook to v3.

    Parameters
    ----------
    nb : NotebookNode
        The Python representation of the notebook to convert.
    """
    if nb.nbformat != 4:
        return nb
    nb.nbformat = v3.nbformat
    nb.nbformat_minor = v3.nbformat_minor
    cells = [ downgrade_cell(cell) for cell in nb.cells ]
    nb.worksheets = [v3.new_worksheet(cells=cells)]
    nb.metadata.setdefault('name', '')
    return nb