"""Test nbformat.validator"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os

from .base import TestsBase
from jsonschema import ValidationError
from IPython.nbformat import read
from ..validator import isvalid, validate


class TestValidator(TestsBase):

    def test_nb2(self):
        """Test that a v2 notebook converted to current passes validation"""
        with self.fopen(u'test2.ipynb', u'r') as f:
            nb = read(f, as_version=4)
        validate(nb)
        self.assertEqual(isvalid(nb), True)

    def test_nb3(self):
        """Test that a v3 notebook passes validation"""
        with self.fopen(u'test3.ipynb', u'r') as f:
            nb = read(f, as_version=4)
        validate(nb)
        self.assertEqual(isvalid(nb), True)

    def test_nb4(self):
        """Test that a v4 notebook passes validation"""
        with self.fopen(u'test4.ipynb', u'r') as f:
            nb = read(f, as_version=4)
        validate(nb)
        self.assertEqual(isvalid(nb), True)

    def test_invalid(self):
        """Test than an invalid notebook does not pass validation"""
        # this notebook has a few different errors:
        # - one cell is missing its source
        # - invalid cell type
        # - invalid output_type
        with self.fopen(u'invalid.ipynb', u'r') as f:
            nb = read(f, as_version=4)
        with self.assertRaises(ValidationError):
            validate(nb)
        self.assertEqual(isvalid(nb), False)

    def test_future(self):
        """Test than a notebook from the future with extra keys passes validation"""
        with self.fopen(u'test4plus.ipynb', u'r') as f:
            nb = read(f, as_version=4)
        with self.assertRaises(ValidationError):
            validate(nb, version=4)
        
        self.assertEqual(isvalid(nb, version=4), False)
        self.assertEqual(isvalid(nb), True)

