# coding: utf-8
"""Tests for the Python API for composing notebook elements"""

import nose.tools as nt

from IPython.nbformat.validator import isvalid, validate, ValidationError
from ..nbbase import (
    NotebookNode, nbformat,
    new_code_cell, new_markdown_cell, new_notebook,
    new_output, new_raw_cell,
)

def test_empty_notebook():
    nb = new_notebook()
    nt.assert_equal(nb.cells, [])
    nt.assert_equal(nb.metadata, NotebookNode())
    nt.assert_equal(nb.nbformat, nbformat)

def test_empty_markdown_cell():
    cell = new_markdown_cell()
    nt.assert_equal(cell.cell_type, 'markdown')
    nt.assert_equal(cell.source, '')

def test_markdown_cell():
    cell = new_markdown_cell(u'* Søme markdown')
    nt.assert_equal(cell.source, u'* Søme markdown')

def test_empty_raw_cell():
    cell = new_raw_cell()
    nt.assert_equal(cell.cell_type, u'raw')
    nt.assert_equal(cell.source, '')

def test_raw_cell():
    cell = new_raw_cell('hi')
    nt.assert_equal(cell.source, u'hi')

def test_empty_code_cell():
    cell = new_code_cell('hi')
    nt.assert_equal(cell.cell_type, 'code')
    nt.assert_equal(cell.source, u'hi')

def test_empty_display_data():
    output = new_output('display_data')
    nt.assert_equal(output.output_type, 'display_data')

def test_empty_stream():
    output = new_output('stream')
    nt.assert_equal(output.output_type, 'stream')
    nt.assert_equal(output.name, 'stdout')
    nt.assert_equal(output.text, '')

def test_empty_execute_result():
    output = new_output('execute_result', execution_count=1)
    nt.assert_equal(output.output_type, 'execute_result')

mimebundle = {
    'text/plain': "some text",
    "application/json": {
        "key": "value"
    },
    "image/svg+xml": 'ABCDEF',
    "application/octet-stream": 'ABC-123',
    "application/vnd.foo+bar": "Some other stuff",
}

def test_display_data():
    output = new_output('display_data', mimebundle)
    for key, expected in mimebundle.items():
        nt.assert_equal(output.data[key], expected)

def test_execute_result():
    output = new_output('execute_result', mimebundle, execution_count=10)
    nt.assert_equal(output.execution_count, 10)
    for key, expected in mimebundle.items():
        nt.assert_equal(output.data[key], expected)

def test_error():
    o = new_output(output_type=u'error', ename=u'NameError',
        evalue=u'Name not found', traceback=[u'frame 0', u'frame 1', u'frame 2']
    )
    nt.assert_equal(o.output_type, u'error')
    nt.assert_equal(o.ename, u'NameError')
    nt.assert_equal(o.evalue, u'Name not found')
    nt.assert_equal(o.traceback, [u'frame 0', u'frame 1', u'frame 2'])

def test_code_cell_with_outputs():
    cell = new_code_cell(execution_count=10, outputs=[
        new_output('display_data', mimebundle),
        new_output('stream', text='hello'),
        new_output('execute_result', mimebundle, execution_count=10),
    ])
    nt.assert_equal(cell.execution_count, 10)
    nt.assert_equal(len(cell.outputs), 3)
    er = cell.outputs[-1]
    nt.assert_equal(er.execution_count, 10)
    nt.assert_equal(er['output_type'], 'execute_result')

def test_stream():
    output = new_output('stream', name='stderr', text='hello there')
    nt.assert_equal(output.name, 'stderr')
    nt.assert_equal(output.text, 'hello there')
