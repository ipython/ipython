"""
Contains tests class for validator.py
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2014  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os

from .base import TestsBase
from jsonschema import SchemaError
from ..current import read
from ..validator import schema_path, isvalid, validate, resolve_ref


#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class TestValidator(TestsBase):

    def test_schema_path(self):
        """Test that the schema path exists"""
        self.assertEqual(os.path.exists(schema_path), True)

    def test_nb2(self):
        """Test that a v2 notebook converted to v3 passes validation"""
        with self.fopen(u'test2.ipynb', u'r') as f:
            nb = read(f, u'json')
        self.assertEqual(validate(nb), [])
        self.assertEqual(isvalid(nb), True)

    def test_nb3(self):
        """Test that a v3 notebook passes validation"""
        with self.fopen(u'test3.ipynb', u'r') as f:
            nb = read(f, u'json')
        self.assertEqual(validate(nb), [])
        self.assertEqual(isvalid(nb), True)

    def test_invalid(self):
        """Test than an invalid notebook does not pass validation"""
        # this notebook has a few different errors:
        # - the name is an integer, rather than a string
        # - one cell is missing its source
        # - one cell has an invalid level
        with self.fopen(u'invalid.ipynb', u'r') as f:
            nb = read(f, u'json')
        self.assertEqual(len(validate(nb)), 3)
        self.assertEqual(isvalid(nb), False)

    def test_resolve_ref(self):
        """Test that references are correctly resolved"""
        # make sure it resolves the ref correctly
        json = {"abc": "def", "ghi": {"$ref": "/abc"}}
        resolved = resolve_ref(json)
        self.assertEqual(resolved, {"abc": "def", "ghi": "def"})

        # make sure it throws an error if the ref is not by itself
        json = {"abc": "def", "ghi": {"$ref": "/abc", "foo": "bar"}}
        with self.assertRaises(SchemaError):
            resolved = resolve_ref(json)

        # make sure it can handle json with no reference
        json = {"abc": "def"}
        resolved = resolve_ref(json)
        self.assertEqual(resolved, json)
