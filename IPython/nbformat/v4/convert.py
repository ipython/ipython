"""Code for converting notebooks to and from v3."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import json

from .nbbase import (
    nbformat, nbformat_minor,
    NotebookNode,
)

from IPython.nbformat import v3
from IPython.utils.log import get_logger


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
    from IPython.nbformat.current import validate, ValidationError
    if from_version == 3:
        # Validate the notebook before conversion
        try:
            validate(nb, version=from_version)
        except ValidationError as e:
            get_logger().error("Notebook JSON is not valid v%i: %s", from_version, e)

        # Mark the original nbformat so consumers know it has been converted
        orig_nbformat = nb.pop('orig_nbformat', None)
        nb.metadata.orig_nbformat = orig_nbformat or 3

        # Mark the new format
        nb.nbformat = nbformat
        nb.nbformat_minor = nbformat_minor

        # remove worksheet(s)
        nb['cells'] = cells = []
        # In the unlikely event of multiple worksheets,
        # they will be flattened
        for ws in nb.pop('worksheets', []):
            # upgrade each cell
            for cell in ws['cells']:
                cells.append(upgrade_cell(cell))
        # upgrade metadata
        nb.metadata.pop('name', '')
        # Validate the converted notebook before returning it
        try:
            validate(nb, version=nbformat)
        except ValidationError as e:
            get_logger().error("Notebook JSON is not valid v%i: %s", nbformat, e)
        return nb
    elif from_version == 4:
        # nothing to do
        if from_minor != nbformat_minor:
            nb.metadata.orig_nbformat_minor = from_minor
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
        - cell.prompt_number -> cell.execution_count
        - update outputs
    """
    cell.setdefault('metadata', NotebookNode())
    if cell.cell_type == 'code':
        cell.pop('language', '')
        cell.metadata.collapsed = cell.pop('collapsed')
        cell.source = cell.pop('input')
        cell.execution_count = cell.pop('prompt_number', None)
        cell.outputs = upgrade_outputs(cell.outputs)
    elif cell.cell_type == 'html':
        # Technically, this exists. It will never happen in practice.
        cell.cell_type = 'markdown'
    return cell

def downgrade_cell(cell):
    """downgrade a cell from v4 to v3

    code cell:
        - set cell.language
        - cell.input <- cell.source
        - cell.prompt_number <- cell.execution_count
        - update outputs
    """
    if cell.cell_type == 'code':
        cell.language = 'python'
        cell.input = cell.pop('source', '')
        cell.prompt_number = cell.pop('execution_count', None)
        cell.collapsed = cell.metadata.pop('collapsed', False)
        cell.outputs = downgrade_outputs(cell.outputs)
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
    - output.type -> output.data.mime/type
    - mime-type keys
    - stream.stream -> stream.name
    """
    output.setdefault('metadata', NotebookNode())
    if output['output_type'] in {'pyout', 'display_data'}:
        if output['output_type'] == 'pyout':
            output['output_type'] = 'execute_result'
            output['execution_count'] = output.pop('prompt_number', None)

        # move output data into data sub-dict
        data = {}
        for key in list(output):
            if key in {'output_type', 'execution_count', 'metadata'}:
                continue
            data[key] = output.pop(key)
        to_mime_key(data)
        output['data'] = data
        to_mime_key(output.metadata)
        if 'application/json' in data:
            data['application/json'] = json.loads(data['application/json'])
        # promote ascii bytes (from v2) to unicode
        for key in ('image/png', 'image/jpeg'):
            if key in data and isinstance(data[key], bytes):
                data[key] = data[key].decode('ascii')
    elif output['output_type'] == 'pyerr':
        output['output_type'] = 'error'
    elif output['output_type'] == 'stream':
        output['name'] = output.pop('stream')
    return output

def downgrade_output(output):
    """downgrade a single code cell output to v3 from v4

    - pyout <- execute_result
    - pyerr <- error
    - output.data.mime/type -> output.type
    - un-mime-type keys
    - stream.stream <- stream.name
    """
    if output['output_type'] in {'execute_result', 'display_data'}:
        if output['output_type'] == 'execute_result':
            output['output_type'] = 'pyout'
            output['prompt_number'] = output.pop('execution_count', None)

        # promote data dict to top-level output namespace
        data = output.pop('data', {})
        if 'application/json' in data:
            data['application/json'] = json.dumps(data['application/json'])
        from_mime_key(data)
        output.update(data)
        from_mime_key(output.get('metadata', {}))
    elif output['output_type'] == 'error':
        output['output_type'] = 'pyerr'
    elif output['output_type'] == 'stream':
        output['stream'] = output.pop('name')
        output.pop('metadata')
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
    from IPython.nbformat.current import validate
    # Validate the notebook before conversion
    validate(nb, version=nbformat)

    if nb.nbformat != 4:
        return nb
    nb.nbformat = v3.nbformat
    nb.nbformat_minor = v3.nbformat_minor
    cells = [ downgrade_cell(cell) for cell in nb.pop('cells') ]
    nb.worksheets = [v3.new_worksheet(cells=cells)]
    nb.metadata.setdefault('name', '')
    nb.metadata.pop('orig_nbformat', None)
    nb.metadata.pop('orig_nbformat_minor', None)

    # Validate the converted notebook before returning it
    validate(nb, version=v3.nbformat)
    return nb
