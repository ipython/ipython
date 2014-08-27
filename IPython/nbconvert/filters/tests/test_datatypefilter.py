"""Module with tests for DataTypeFilter"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from ...tests.base import TestsBase
from ..datatypefilter import DataTypeFilter


class TestDataTypeFilter(TestsBase):
    """Contains test functions for datatypefilter.py"""

    def test_constructor(self):
        """Can an instance of a DataTypeFilter be created?"""
        DataTypeFilter()

    def test_junk_types(self):
        """Can the DataTypeFilter pickout a useful type from a list of junk types?"""
        filter = DataTypeFilter()
        assert "image/png" in filter(["hair", "water", "image/png", "rock"])
        assert "application/pdf" in filter(["application/pdf", "hair", "water", "png", "rock"])
        self.assertEqual(filter(["hair", "water", "rock"]), [])

    def test_null(self):
        """Will the DataTypeFilter fail if no types are passed in?"""
        filter = DataTypeFilter()
        self.assertEqual(filter([]), [])
