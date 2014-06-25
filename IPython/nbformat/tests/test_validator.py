"""Test nbformat.validator"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os

from .base import TestsBase
from jsonschema import ValidationError
from ..current import read
from ..validator import isvalid, validate


#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class TestValidator(TestsBase):

    def test_nb2(self):
        """Test that a v2 notebook converted to v3 passes validation"""
        with self.fopen(u'test2.ipynb', u'r') as f:
            nb = read(f, u'json')
        validate(nb)
        self.assertEqual(isvalid(nb), True)

    def test_nb3(self):
        """Test that a v3 notebook passes validation"""
        with self.fopen(u'test3.ipynb', u'r') as f:
            nb = read(f, u'json')
        validate(nb)
        self.assertEqual(isvalid(nb), True)

    def test_invalid(self):
        """Test than an invalid notebook does not pass validation"""
        # this notebook has a few different errors:
        # - the name is an integer, rather than a string
        # - one cell is missing its source
        # - one cell has an invalid level
        with self.fopen(u'invalid.ipynb', u'r') as f:
            nb = read(f, u'json')
        with self.assertRaises(ValidationError):
            validate(nb)
        self.assertEqual(isvalid(nb), False)

