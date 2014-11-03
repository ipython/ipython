"""Tests for nbformat validation"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import io
import os

import nose.tools as nt

from IPython.nbformat.validator import validate, ValidationError
from ..nbjson import reads
from ..nbbase import (
    nbformat,
    new_code_cell, new_markdown_cell, new_notebook,
    new_output, new_raw_cell,
)

def validate4(obj, ref=None):
    return validate(obj, ref, version=nbformat)

def test_valid_code_cell():
    cell = new_code_cell()
    validate4(cell, 'code_cell')

def test_invalid_code_cell():
    cell = new_code_cell()

    cell['source'] = 5
    with nt.assert_raises(ValidationError):
        validate4(cell, 'code_cell')

    cell = new_code_cell()
    del cell['metadata']

    with nt.assert_raises(ValidationError):
        validate4(cell, 'code_cell')

    cell = new_code_cell()
    del cell['source']

    with nt.assert_raises(ValidationError):
        validate4(cell, 'code_cell')

    cell = new_code_cell()
    del cell['cell_type']

    with nt.assert_raises(ValidationError):
        validate4(cell, 'code_cell')

def test_invalid_markdown_cell():
    cell = new_markdown_cell()

    cell['source'] = 5
    with nt.assert_raises(ValidationError):
        validate4(cell, 'markdown_cell')

    cell = new_markdown_cell()
    del cell['metadata']

    with nt.assert_raises(ValidationError):
        validate4(cell, 'markdown_cell')

    cell = new_markdown_cell()
    del cell['source']

    with nt.assert_raises(ValidationError):
        validate4(cell, 'markdown_cell')

    cell = new_markdown_cell()
    del cell['cell_type']

    with nt.assert_raises(ValidationError):
        validate4(cell, 'markdown_cell')

def test_invalid_raw_cell():
    cell = new_raw_cell()

    cell['source'] = 5
    with nt.assert_raises(ValidationError):
        validate4(cell, 'raw_cell')

    cell = new_raw_cell()
    del cell['metadata']

    with nt.assert_raises(ValidationError):
        validate4(cell, 'raw_cell')

    cell = new_raw_cell()
    del cell['source']

    with nt.assert_raises(ValidationError):
        validate4(cell, 'raw_cell')

    cell = new_raw_cell()
    del cell['cell_type']

    with nt.assert_raises(ValidationError):
        validate4(cell, 'raw_cell')

def test_sample_notebook():
    here = os.path.dirname(__file__)
    with io.open(os.path.join(here, os.pardir, os.pardir, 'tests', "test4.ipynb"), encoding='utf-8') as f:
        nb = reads(f.read())
    validate4(nb)
